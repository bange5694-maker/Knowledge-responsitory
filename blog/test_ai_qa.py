"""
M1 单元测试：Article AI 字段、AI 状态 stale 规则、AIClient。

契约来源（只依据以下文档，不读实现文件）：
- doc/第9-10周任务/_tdd/M1.md 第 3/4/5/6 节
- doc/第9-10周任务/AI功能规格说明.md 2.1、2.2
- doc/第9-10周任务/实施计划-丁昊-AI问答.md 4、5、11.1、11.2、12.1

AI 调用只 mock `djangoblog.ai.client.OpenAI`，不真实访问 DeepSeek。
"""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from blog.models import Article
from djangoblog.ai import AIClient, AIClientError
from djangoblog.test_base import BaseTestCase


def _completion(content):
    """构造 OpenAI 兼容响应：choices[0].message.content。"""
    return SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content=content))
        ]
    )


class ArticleAIFieldsTest(BaseTestCase):
    """SPEC: _tdd/M1.md §3.1、§4.1；AI功能规格说明 §2.1。"""

    def test_ai_field_defaults(self):
        """SPEC: M1 §4.1.1 / §3.1 —— 七个 AI 字段的默认值。"""
        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_summary, '')
        self.assertEqual(self.article.ai_highlights, [])
        self.assertEqual(self.article.ai_audience, '')
        self.assertEqual(self.article.ai_keywords, [])
        self.assertEqual(self.article.ai_status, 'pending')
        self.assertIsNone(self.article.ai_generated_at)
        self.assertEqual(self.article.ai_model, '')

    def test_ai_status_choices(self):
        """SPEC: M1 §4.1.2 / §3.1 —— 状态值集合必须精确匹配。"""
        self.assertEqual(
            {choice[0] for choice in Article.AI_STATUS_CHOICES},
            {'pending', 'done', 'failed', 'stale'},
        )

    def test_json_defaults_are_independent(self):
        """SPEC: M1 §4.1.3 / §3.1 —— JSON 默认 list 不得是共享可变对象。"""
        article_a = Article(
            title='未保存A',
            body='正文A',
            author=self.user,
            category=self.category,
        )
        article_b = Article(
            title='未保存B',
            body='正文B',
            author=self.user,
            category=self.category,
        )

        article_a.ai_keywords.append('python')

        self.assertEqual(article_a.ai_keywords, ['python'])
        self.assertEqual(article_b.ai_keywords, [])


class ArticleAIStaleTest(BaseTestCase):
    """SPEC: _tdd/M1.md §3.2、§4.2；实施计划 §4.2、§11.1。"""

    def _mark_done(self):
        """前置：把 BaseTestCase 提供的文章置为 done 并确认已落库。"""
        self.article.ai_status = 'done'
        self.article.save()
        self.article.refresh_from_db()
        self.assertEqual(self.article.ai_status, 'done')

    def test_done_title_change_sets_stale(self):
        """SPEC: M1 §4.2.1 / §3.2(2) —— done 后改标题保存 → stale。"""
        self._mark_done()

        self.article.title = '修改后的标题'
        self.article.save()
        self.article.refresh_from_db()

        self.assertEqual(self.article.ai_status, 'stale')
        self.assertEqual(self.article.title, '修改后的标题')

    def test_done_body_change_sets_stale(self):
        """SPEC: M1 §4.2.2 / §3.2(3) —— done 后改正文保存 → stale。"""
        self._mark_done()

        self.article.body = '修改后的正文'
        self.article.save()
        self.article.refresh_from_db()

        self.assertEqual(self.article.ai_status, 'stale')
        self.assertEqual(self.article.body, '修改后的正文')

    def test_done_unchanged_stays_done(self):
        """SPEC: M1 §4.2.3 / §3.2(4) —— done 且标题/正文未变，再保存仍是 done。"""
        self._mark_done()

        self.article.save()
        self.article.refresh_from_db()

        self.assertEqual(self.article.ai_status, 'done')

    def test_views_update_does_not_set_stale(self):
        """SPEC: M1 §4.2.4 / §3.2(5) —— 浏览量更新路径不改变 ai_status。"""
        self._mark_done()

        self.article.views += 1
        self.article.save(update_fields=['views'])
        self.article.refresh_from_db()

        self.assertEqual(self.article.ai_status, 'done')

    def test_update_fields_title_persists_stale(self):
        """SPEC: M1 §4.2.5 / §3.2(6) —— update_fields=['title'] 时 stale 也要落库。"""
        self._mark_done()

        self.article.title = '仅更新标题'
        self.article.save(update_fields=['title'])
        self.article.refresh_from_db()

        self.assertEqual(self.article.title, '仅更新标题')
        self.assertEqual(self.article.ai_status, 'stale')

    def test_non_done_status_not_changed(self):
        """SPEC: M1 §4.2.6 / §3.2(7) —— 非 done 状态改标题后状态保持原值。"""
        for status in ('pending', 'failed', 'stale'):
            with self.subTest(status=status):
                self.article.ai_status = status
                self.article.save()

                self.article.title = f'标题-{status}-已修改'
                self.article.save()
                self.article.refresh_from_db()

                self.assertEqual(self.article.ai_status, status)


# 用显式的非默认配置验证 AIClient 确实逐次读取 settings。
AI_TEST_SETTINGS = dict(
    AI_ENABLED=True,
    AI_API_KEY='sk-test-key',
    AI_BASE_URL='https://ai-unit.test/v1',
    AI_MODEL='unit-test-model',
    AI_TIMEOUT=17,
    AI_MAX_TOKENS=512,
)

MESSAGES = [{'role': 'user', 'content': 'hi'}]


@override_settings(**AI_TEST_SETTINGS)
class AIClientTest(SimpleTestCase):
    """SPEC: _tdd/M1.md §3.3、§4.3、§5；AI功能规格说明 §2.2。"""

    def _stub_success(self, mock_openai, content=' 你好 '):
        """让 mock 出来的 OpenAI 客户端返回一个成功的 completion。"""
        fake_client = mock_openai.return_value
        fake_client.chat.completions.create.return_value = _completion(content)
        return fake_client

    def test_disabled_raises_and_does_not_create_client(self):
        """SPEC: M1 §4.3.1 / §3.3 —— AI_ENABLED 假 → AIClientError 且不建客户端。"""
        with override_settings(AI_ENABLED=False):
            with patch('djangoblog.ai.client.OpenAI') as mock_openai:
                with self.assertRaises(AIClientError):
                    AIClient.chat(MESSAGES)
                mock_openai.assert_not_called()

    def test_missing_key_raises_and_does_not_create_client(self):
        """SPEC: M1 §4.3.2 / §3.3 —— API Key 为空 → AIClientError 且不建客户端。"""
        with override_settings(AI_ENABLED=True, AI_API_KEY=''):
            with patch('djangoblog.ai.client.OpenAI') as mock_openai:
                with self.assertRaises(AIClientError):
                    AIClient.chat(MESSAGES)
                mock_openai.assert_not_called()

    def test_success_returns_stripped_content(self):
        """SPEC: M1 §4.3.3 / §3.3 —— 返回 choices[0].message.content.strip()。"""
        with patch('djangoblog.ai.client.OpenAI') as mock_openai:
            self._stub_success(mock_openai, content=' 你好 ')
            result = AIClient.chat(MESSAGES)

        self.assertEqual(result, '你好')

    def test_client_constructor_options(self):
        """SPEC: M1 §4.3.4 / §3.3 —— OpenAI(api_key, base_url, timeout, max_retries=2)。"""
        with patch('djangoblog.ai.client.OpenAI') as mock_openai:
            self._stub_success(mock_openai)
            AIClient.chat(MESSAGES)

            mock_openai.assert_called_once()
            kwargs = mock_openai.call_args.kwargs
            self.assertEqual(kwargs['api_key'], 'sk-test-key')
            self.assertEqual(kwargs['base_url'], 'https://ai-unit.test/v1')
            self.assertEqual(kwargs['timeout'], 17)
            self.assertEqual(kwargs['max_retries'], 2)

    def test_create_call_options(self):
        """SPEC: M1 §4.3.5 / §3.3 —— create 收到 model/messages/temperature/max_tokens。"""
        messages = [
            {'role': 'system', 'content': '系统提示'},
            {'role': 'user', 'content': '你好'},
        ]
        with patch('djangoblog.ai.client.OpenAI') as mock_openai:
            fake_client = self._stub_success(mock_openai, content='OK')
            AIClient.chat(messages)

            create = fake_client.chat.completions.create
            create.assert_called_once()
            kwargs = create.call_args.kwargs
            self.assertEqual(kwargs['model'], 'unit-test-model')
            self.assertEqual(kwargs['messages'], messages)
            self.assertEqual(kwargs['temperature'], 0.3)
            self.assertEqual(kwargs['max_tokens'], 512)

    def test_custom_temperature_and_max_tokens(self):
        """SPEC: M1 §4.3.6 / §3.3 —— 自定义 temperature/max_tokens 原样透传。"""
        with patch('djangoblog.ai.client.OpenAI') as mock_openai:
            fake_client = self._stub_success(mock_openai)
            AIClient.chat(MESSAGES, temperature=0.9, max_tokens=64)

            kwargs = fake_client.chat.completions.create.call_args.kwargs
            self.assertEqual(kwargs['temperature'], 0.9)
            self.assertEqual(kwargs['max_tokens'], 64)

    def test_max_tokens_defaults_to_setting(self):
        """SPEC: M1 §4.3.7 / §3.3 —— max_tokens=None 时使用 settings.AI_MAX_TOKENS。"""
        with override_settings(AI_MAX_TOKENS=1234):
            with patch('djangoblog.ai.client.OpenAI') as mock_openai:
                fake_client = self._stub_success(mock_openai)
                AIClient.chat(MESSAGES)

                kwargs = fake_client.chat.completions.create.call_args.kwargs
                self.assertEqual(kwargs['max_tokens'], 1234)

    def test_upstream_error_wrapped_and_no_key(self):
        """SPEC: M1 §4.3.8 / §3.3 —— 上游异常统一为 AIClientError，消息不含 Key。"""
        with patch('djangoblog.ai.client.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = Exception('boom')
            with self.assertRaises(AIClientError) as ctx:
                AIClient.chat(MESSAGES)

        self.assertNotIn('sk-test-key', str(ctx.exception))

    def test_timeout_error_wrapped(self):
        """SPEC: M1 §4.3.9 / §3.3 —— 超时异常转 AIClientError，消息不含 Key。"""
        with patch('djangoblog.ai.client.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = TimeoutError('timed out')
            with self.assertRaises(AIClientError) as ctx:
                AIClient.chat(MESSAGES)

        self.assertNotIn('sk-test-key', str(ctx.exception))

    def test_empty_content_raises(self):
        """SPEC: M1 §4.3.10 / §3.3 —— content 为 None 或 '' 时抛 AIClientError。"""
        for content in (None, ''):
            with self.subTest(content=content):
                with patch('djangoblog.ai.client.OpenAI') as mock_openai:
                    self._stub_success(mock_openai, content=content)
                    with self.assertRaises(AIClientError):
                        AIClient.chat(MESSAGES)


# =============================================================================
# M2：CommentIndex + 普通搜索隔离
#
# 契约来源：
# - doc/第9-10周任务/_tdd/M2.md §3.1、§3.2、§3.3、§4
# - doc/第9-10周任务/AI功能规格说明.md §4.5、§4.6
# - doc/第9-10周任务/实施计划-丁昊-AI问答.md §6、§11.3、§11.4、§12.1
#
# 说明：
# - `CommentIndex` 在 M2 实现前不存在，因此只在 `CommentIndexTest.setUp`
#   内部导入，避免 M1 测试在模块导入阶段一起失败。
# - 普通搜索测试只检查 `form.searchqueryset.query.models`，不调用
#   `form.search()`，不触发真实 Whoosh 查询。
# =============================================================================

from django.template.loader import render_to_string  # noqa: E402
from django.test import RequestFactory, TestCase  # noqa: E402

from haystack.query import SearchQuerySet  # noqa: E402

from blog.views import EsSearchView  # noqa: E402
from comments.models import Comment  # noqa: E402


class CommentIndexTest(BaseTestCase):
    """SPEC: _tdd/M2.md §3.1、§3.2、§4.1；AI功能规格说明 §4.5。"""

    def setUp(self):
        super().setUp()
        # M2 实现前 ImportError 属于预期的红；放在 setUp 避免污染 M1 导入。
        from blog.search_indexes import CommentIndex

        self.index = CommentIndex()

    def _create_comment(self, body, article=None, is_enable=True):
        """直接用 ORM 创建评论，显式设置 is_enable（不依赖 create_comment 默认值）。"""
        return Comment.objects.create(
            body=body,
            author=self.user,
            article=article if article is not None else self.article,
            is_enable=is_enable,
        )

    def _reload_comment(self, comment):
        """重新取 comment（连带 author/article），避免读到缓存的旧 author。"""
        return Comment.objects.select_related('author', 'article').get(pk=comment.pk)

    def test_get_model_returns_comment(self):
        """SPEC: M2 §3.1 / §4.1.1 —— get_model() 返回 comments.models.Comment。"""
        self.assertIs(self.index.get_model(), Comment)

    def test_index_queryset_only_enabled_comments_on_published_articles(self):
        """SPEC: M2 §3.1 / §4.1.2；实施计划 §11.3 —— 仅 is_enable=True 且文章 status='p'。"""
        published_enabled = self._create_comment('已发布-启用评论', is_enable=True)
        published_disabled = self._create_comment('已发布-禁用评论', is_enable=False)

        draft = self.create_article(title='草稿文章', status='d')
        draft_enabled = self._create_comment(
            '草稿-启用评论', article=draft, is_enable=True
        )
        draft_disabled = self._create_comment(
            '草稿-禁用评论', article=draft, is_enable=False
        )

        ids = set(self.index.index_queryset().values_list('id', flat=True))

        self.assertEqual(
            ids,
            {published_enabled.id},
            msg=(
                'index_queryset 应只含“已发布文章 + is_enable=True”的评论；'
                f'被排除的评论 id: {published_disabled.id}, '
                f'{draft_enabled.id}, {draft_disabled.id}'
            ),
        )

    def test_index_template_includes_title_body_author(self):
        """SPEC: M2 §3.2 / §4.1.3 —— 索引模板渲染出文章标题、评论正文、作者昵称/用户名。"""
        body = '这是评论正文-唯一片段'
        comment = self._create_comment(body=body)

        self.user.nickname = '模板昵称'
        self.user.save(update_fields=['nickname'])
        comment = self._reload_comment(comment)

        rendered = render_to_string(
            'search/indexes/comments/comment_text.txt', {'object': comment}
        )

        self.assertIn(self.article.title, rendered)
        self.assertIn(body, rendered)
        self.assertIn(self.user.username, rendered)
        self.assertIn('模板昵称', rendered)

    def test_prepare_author_prefers_nickname(self):
        """SPEC: M2 §3.1 / §4.1.4 —— 昵称非空时 prepare_author 返回昵称。"""
        comment = self._create_comment('昵称优先评论')

        self.user.nickname = '测试昵称'
        self.user.save(update_fields=['nickname'])
        comment = self._reload_comment(comment)

        self.assertEqual(self.index.prepare_author(comment), '测试昵称')

    def test_prepare_author_falls_back_to_username(self):
        """SPEC: M2 §3.1 / §4.1.5 —— 昵称为空时 prepare_author 回退到 username。"""
        comment = self._create_comment('昵称回退评论')

        self.user.nickname = ''
        self.user.save(update_fields=['nickname'])
        comment = self._reload_comment(comment)

        self.assertEqual(self.index.prepare_author(comment), self.user.username)

    def test_prepare_article_title(self):
        """SPEC: M2 §3.1 / §4.1.6 —— prepare_article_title 返回所属文章标题。"""
        comment = self._create_comment('文章标题评论')

        self.assertEqual(
            self.index.prepare_article_title(comment), self.article.title
        )


class SearchIsolationTest(TestCase):
    """SPEC: _tdd/M2.md §3.3、§4.2；实施计划 §6.3、§11.4；AI功能规格说明 §4.6。"""

    def setUp(self):
        self.factory = RequestFactory()

    def _build_form(self, view):
        """构造 request 后调用 build_form；不执行 form.search()。"""
        view.request = self.factory.get('/search/', {'q': 'test'})
        return view.build_form()

    def test_build_form_limits_to_article_without_searchqueryset(self):
        """SPEC: M2 §3.3 / §4.2.1 —— 无 searchqueryset 时也只搜 Article。"""
        form = self._build_form(EsSearchView())

        self.assertEqual(form.searchqueryset.query.models, {Article})

    def test_build_form_limits_to_article_with_searchqueryset(self):
        """SPEC: M2 §3.3 / §4.2.2 —— 已有 searchqueryset 时仍限制为 Article。"""
        form = self._build_form(EsSearchView(searchqueryset=SearchQuerySet()))

        self.assertEqual(form.searchqueryset.query.models, {Article})

    def test_comment_model_not_in_search_models(self):
        """SPEC: M2 §4.2.3；AI功能规格说明 §4.6 —— 普通搜索集合不含 Comment。"""
        form = self._build_form(EsSearchView())

        self.assertNotIn(Comment, form.searchqueryset.query.models)
