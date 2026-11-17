# 何君杰: AI 导读测试，覆盖成功、失败、stale、隐藏四条路径（规格 3.9）
import json
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.template.loader import render_to_string
from django.test import TestCase, override_settings

from blog.ai_summary import generate_ai_summary
from blog.models import Article
from djangoblog.test_base import BaseTestCase


# 一份合法的 AI 返回 JSON，供多个测试复用
VALID_AI_JSON = json.dumps({
    'summary': '这篇文章用三个案例讲清了 Django 缓存的分层设计，包括缓存穿透、缓存击穿以及缓存雪崩的防范策略。它详细分析了 Cache Aside 模式在不同并发场景下的表现，适合正在做性能优化、希望解决高并发下数据一致性问题的 Django 后端开发者阅读。',
    'highlights': [
        '用 Cache Aside 解决读写不一致',
        '用 TTL 兜底防止脏数据常驻',
        '用 Redis 单线程模型解释 INCR 原子性',
    ],
    'audience': '正在做缓存优化的 Django 后端开发者',
    'keywords': ['Django', 'Redis', '缓存一致性'],
}, ensure_ascii=False)


class AISummaryServiceTest(BaseTestCase):
    """何君杰: generate_ai_summary 的生成、失败、force、跳过规则。"""

    def setUp(self):
        super().setUp()
        # 确保是一篇已发布文章，避免 BaseTestCase 的默认值干扰
        self.article.status = 'p'
        self.article.type = 'a'
        self.article.ai_status = 'pending'
        self.article.save()

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_success_writes_fields_and_done(self, mock_chat):
        """成功：4 个字段写入，ai_status=done，生成时间和模型名落库。"""
        ok = generate_ai_summary(self.article, force=False)

        self.assertTrue(ok)
        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_status, 'done')
        self.assertIn('Django 缓存', self.article.ai_summary)
        self.assertEqual(len(self.article.ai_highlights), 3)
        self.assertEqual(self.article.ai_audience, '正在做缓存优化的 Django 后端开发者')
        self.assertEqual(self.article.ai_keywords, ['Django', 'Redis', '缓存一致性'])
        self.assertIsNotNone(self.article.ai_generated_at)
        self.assertTrue(self.article.ai_model)
        mock_chat.assert_called_once()

    @patch('blog.ai_summary.AIClient.chat', side_effect=Exception('boom'))
    def test_ai_error_sets_failed_and_returns_false(self, mock_chat):
        """失败：AI 抛异常 → ai_status=failed，返回 False，不向外抛。"""
        ok = generate_ai_summary(self.article, force=False)

        self.assertFalse(ok)
        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_status, 'failed')
        self.assertEqual(self.article.ai_summary, '')

    @patch('blog.ai_summary.AIClient.chat', return_value='这不是 JSON')
    def test_invalid_json_sets_failed(self, mock_chat):
        """失败：返回非 JSON → 视为失败，不把半截内容写库。"""
        ok = generate_ai_summary(self.article, force=False)

        self.assertFalse(ok)
        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_status, 'failed')
        self.assertEqual(self.article.ai_summary, '')

    @patch('blog.ai_summary.AIClient.chat', return_value=json.dumps({
        'summary': '短',
        'highlights': ['只有一条'],
        'audience': '',
        'keywords': ['a'],
    }, ensure_ascii=False))
    def test_field_validation_fails(self, mock_chat):
        """失败：字段不满足约束（看点不足 3 条/关键词不足 3 个）→ failed。"""
        ok = generate_ai_summary(self.article, force=False)

        self.assertFalse(ok)
        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_status, 'failed')

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_skip_done_without_force(self, mock_chat):
        """跳过：done 且 force=False 时不调用 AI。"""
        self.article.ai_status = 'done'
        self.article.ai_summary = '旧摘要'
        self.article.save()

        ok = generate_ai_summary(self.article, force=False)

        self.assertTrue(ok)
        mock_chat.assert_not_called()
        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_summary, '旧摘要')

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_force_regenerates_done(self, mock_chat):
        """force=True：done 的文章也重新生成。"""
        self.article.ai_status = 'done'
        self.article.ai_summary = '旧摘要'
        self.article.save()

        ok = generate_ai_summary(self.article, force=True)

        self.assertTrue(ok)
        mock_chat.assert_called_once()
        self.article.refresh_from_db()
        self.assertNotEqual(self.article.ai_summary, '旧摘要')

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_skip_draft(self, mock_chat):
        """跳过：草稿不生成。"""
        self.article.status = 'd'
        self.article.save()

        ok = generate_ai_summary(self.article, force=False)

        self.assertFalse(ok)
        mock_chat.assert_not_called()

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_skip_page_type(self, mock_chat):
        """跳过：独立页面（type='p'）不生成。"""
        self.article.type = 'p'
        self.article.save()

        ok = generate_ai_summary(self.article, force=False)

        self.assertFalse(ok)
        mock_chat.assert_not_called()

    def test_stale_after_body_change(self):
        """过期：done 后改正文 → ai_status 变 stale（模型层规则）。"""
        self.article.ai_status = 'done'
        self.article.ai_summary = '旧摘要'
        self.article.save()

        self.article.body = self.article.body + '\n\n新增一段正文'
        self.article.save()
        self.article.refresh_from_db()

        self.assertEqual(self.article.ai_status, 'stale')


class AISummaryTemplateTest(TestCase):
    """何君杰: _ai_summary.html 的展示与隐藏规则（规格 3.4 / 3.8）。"""

    def _make_article(self, **kwargs):
        """构造一个内存 Article，不落库，专测模板渲染。"""
        defaults = dict(
            title='测试文章',
            body='正文',
            ai_status='done',
            ai_summary='这是一段摘要',
            ai_highlights=['看点一', '看点二', '看点三'],
            ai_audience='后端开发者',
            ai_keywords=['Django', 'Redis'],
        )
        defaults.update(kwargs)
        return Article(**defaults)

    def _render(self, article):
        return render_to_string('blog/_ai_summary.html', {'article': article})

    def test_done_shows_card(self):
        """done 且摘要非空 → 卡片出现，包含摘要、看点、受众、关键词。"""
        html = self._render(self._make_article())

        self.assertIn('AI 导读', html)
        self.assertIn('这是一段摘要', html)
        self.assertIn('看点一', html)
        self.assertIn('后端开发者', html)
        self.assertIn('Django', html)

    def test_pending_hides_card(self):
        """pending → 卡片不出现。"""
        html = self._render(self._make_article(ai_status='pending'))
        self.assertNotIn('AI 导读', html)

    def test_stale_hides_card(self):
        """stale → 卡片不出现。"""
        html = self._render(self._make_article(ai_status='stale'))
        self.assertNotIn('AI 导读', html)

    def test_failed_hides_card(self):
        """failed → 卡片不出现。"""
        html = self._render(self._make_article(ai_status='failed'))
        self.assertNotIn('AI 导读', html)

    def test_empty_summary_hides_card(self):
        """done 但摘要为空 → 视为字段全缺失，卡片隐藏。"""
        html = self._render(self._make_article(ai_summary=''))
        self.assertNotIn('AI 导读', html)

    def test_empty_audience_hides_row(self):
        """受众为空 → “适合谁读”整行隐藏，但卡片和看点还在。"""
        html = self._render(self._make_article(ai_audience=''))

        self.assertIn('AI 导读', html)
        self.assertIn('看点一', html)
        self.assertNotIn('适合谁读', html)

    def test_empty_keywords_hides_row(self):
        """关键词为空 → 关键词整行隐藏。"""
        html = self._render(self._make_article(ai_keywords=[]))

        self.assertIn('AI 导读', html)
        self.assertNotIn('关键词', html)

    def test_highlights_less_than_three(self):
        """看点不足 3 条 → 不报错，有几条显示几条。"""
        html = self._render(self._make_article(ai_highlights=['只有一条']))

        self.assertIn('只有一条', html)
        self.assertIn('AI 导读', html)


@override_settings(AI_ENABLED=True)
class GenerateAICommandTest(BaseTestCase):
    """何君杰: generate_ai_content 管理命令的参数与统计。"""

    def setUp(self):
        super().setUp()
        self.article.status = 'p'
        self.article.type = 'a'
        self.article.ai_status = 'pending'
        self.article.save()

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_article_id_generates_one(self, mock_chat):
        """--article-id 只处理指定文章。"""
        call_command('generate_ai_content', article_id=self.article.pk, sleep=0)

        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_status, 'done')
        mock_chat.assert_called_once()

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_all_skips_done_without_force(self, mock_chat):
        """--all 默认跳过 done 的文章。"""
        self.article.ai_status = 'done'
        self.article.save()

        call_command('generate_ai_content', all=True, sleep=0)

        mock_chat.assert_not_called()

    @patch('blog.ai_summary.AIClient.chat', return_value=VALID_AI_JSON)
    def test_all_force_regenerates_done(self, mock_chat):
        """--all --force 重新生成 done 的文章。"""
        self.article.ai_status = 'done'
        self.article.save()

        call_command('generate_ai_content', all=True, force=True, sleep=0)

        mock_chat.assert_called_once()

    def test_missing_scope_raises(self):
        """不给 --all 也不给 --article-id → CommandError。"""
        with self.assertRaises(CommandError):
            call_command('generate_ai_content')

    def test_both_scopes_raises(self):
        """--all 与 --article-id 同时给 → CommandError。"""
        with self.assertRaises(CommandError):
            call_command('generate_ai_content', all=True, article_id=self.article.pk)

    def test_nonexistent_article_raises(self):
        """--article-id 指向不存在的文章 → CommandError。"""
        with self.assertRaises(CommandError):
            call_command('generate_ai_content', article_id=999999)

    def test_draft_article_raises(self):
        """--article-id 指向草稿 → CommandError。"""
        self.article.status = 'd'
        self.article.save()

        with self.assertRaises(CommandError):
            call_command('generate_ai_content', article_id=self.article.pk)