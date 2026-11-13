# HJJ: Django管理命令 - 通知百度收录URL
# 通过 python manage.py baidu_notify {data_type} 执行
# 向百度搜索推送站点URL，加快收录速度

from django.core.management.base import BaseCommand

from djangoblog.spider_notify import SpiderNotify
from djangoblog.utils import get_current_site
from blog.models import Article, Tag, Category

# HJJ: 获取当前站点域名
site = get_current_site().domain


class Command(BaseCommand):
    # HJJ: 命令帮助信息
    help = 'notify baidu url'

    def add_arguments(self, parser):
        """
        HJJ: 添加命令行参数
        
        参数:
            data_type: str - 推送数据类型
                可选值: 'all' | 'article' | 'tag' | 'category'
                - article: 推送所有已发布文章
                - tag: 推送所有标签页
                - category: 推送所有分类页
                - all: 推送以上全部
        """
        parser.add_argument(
            'data_type',
            type=str,
            choices=[
                'all',
                'article',
                'tag',
                'category'],
            help='article : all article,tag : all tag,category: all category,all: All of these')

    def get_full_url(self, path):
        """
        HJJ: 将相对路径转换为完整URL
        
        参数:
            path: str - 相对路径（如 /article/123.html）
        返回:
            str - 完整URL（如 https://example.com/article/123.html）
        """
        url = "https://{site}{path}".format(site=site, path=path)
        return url

    def handle(self, *args, **options):
        """
        HJJ: 命令入口方法
        
        执行流程：
        1. 根据data_type参数收集需要推送的URL列表
        2. 调用SpiderNotify向百度推送URL
        
        参数:
            *args: 位置参数（暂未使用）
            **options: 关键字参数（包含data_type）
        返回:
            无
        """
        type = options['data_type']
        self.stdout.write('start get %s' % type)

        urls = []
        
        # HJJ: 收集已发布文章的URL
        if type == 'article' or type == 'all':
            for article in Article.objects.filter(status='p'):
                urls.append(article.get_full_url())
        
        # HJJ: 收集所有标签页的URL
        if type == 'tag' or type == 'all':
            for tag in Tag.objects.all():
                url = tag.get_absolute_url()
                urls.append(self.get_full_url(url))
        
        # HJJ: 收集所有分类页的URL
        if type == 'category' or type == 'all':
            for category in Category.objects.all():
                url = category.get_absolute_url()
                urls.append(self.get_full_url(url))

        # HJJ: 输出推送数量并执行推送
        self.stdout.write(
            self.style.SUCCESS(
                'start notify %d urls' %
                len(urls)))
        SpiderNotify.baidu_notify(urls)
        self.stdout.write(self.style.SUCCESS('finish notify'))