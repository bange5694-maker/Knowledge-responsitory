# 何君杰: AI 导读批量生成命令
# 用法：
#   python manage.py generate_ai_content --all
#   python manage.py generate_ai_content --article-id 1
#   python manage.py generate_ai_content --all --force

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from blog.ai_summary import generate_ai_summary
from blog.models import Article


class Command(BaseCommand):
    help = '生成或重新生成文章的 AI 导读'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='处理所有已发布文章（status=p, type=a）',
        )
        parser.add_argument(
            '--article-id',
            type=int,
            default=None,
            help='只处理指定 ID 的文章',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='已生成（ai_status=done）的文章也重新生成',
        )
        parser.add_argument(
            '--sleep',
            type=float,
            default=1.0,
            help='每篇之间的间隔秒数，默认 1 秒（防限流），设 0 关闭',
        )

    def handle(self, *args, **options):
        # 何君杰: AI 未启用时直接退出，避免每篇都失败还白等
        if not getattr(settings, 'AI_ENABLED', False):
            raise CommandError('AI_ENABLED=False，AI 功能未启用，无法生成导读')

        run_all = options['all']
        article_id = options['article_id']
        force = options['force']
        sleep_seconds = options['sleep']

        # 何君杰: 必须且只能指定一种范围
        if not run_all and article_id is None:
            raise CommandError('请指定 --all 或 --article-id')
        if run_all and article_id is not None:
            raise CommandError('--all 与 --article-id 不能同时使用')

        # 何君杰: 只处理已发布文章（规格 3.2 / 3.6）
        queryset = Article.objects.filter(status='p', type='a')

        if article_id is not None:
            raw = Article.objects.filter(pk=article_id).first()
            if raw is None:
                raise CommandError(f'文章 {article_id} 不存在')
            if raw.status != 'p' or raw.type != 'a':
                raise CommandError(
                    f'文章 {article_id} 不是已发布文章（当前 status={raw.status}, type={raw.type}）'
                )
            queryset = queryset.filter(pk=article_id)

        # 何君杰: 非 force 时跳过已 done 的文章，避免重复花钱
        if not force:
            queryset = queryset.exclude(ai_status='done')

        articles = list(queryset.order_by('pk'))
        total = len(articles)
        if total == 0:
            self.stdout.write(self.style.WARNING('没有需要处理的文章'))
            return

        self.stdout.write(
            f'开始处理 {total} 篇文章（force={force}, sleep={sleep_seconds}s）...'
        )

        ok = fail = 0
        for index, article in enumerate(articles, start=1):
            self.stdout.write(
                f'[{index}/{total}] 《{article.title}》(id={article.pk}, '
                f'ai_status={article.ai_status}) ...'
            )
            if generate_ai_summary(article, force=force):
                ok += 1
                self.stdout.write(self.style.SUCCESS('  成功'))
            else:
                fail += 1
                self.stdout.write(self.style.ERROR('  失败'))

            # 最后一篇不用等
            if index < total and sleep_seconds > 0:
                time.sleep(sleep_seconds)

        self.stdout.write(
            self.style.SUCCESS(f'完成：成功 {ok} 篇，失败 {fail} 篇，共 {total} 篇')
        )