# HJJ: 博客核心数据模型模块，定义了文章、分类、标签、友情链接、侧边栏、站点配置等ORM模型，
# HJJ: 包含缓存策略、SEO友好URL生成、浏览计数、评论缓存等核心业务逻辑

import logging
import re
from abc import abstractmethod

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from mdeditor.fields import MDTextField
from uuslug import slugify

from djangoblog.utils import cache_decorator, cache
from djangoblog.utils import get_current_site
from djangoblog.constants import CacheTimeout, CacheKey

logger = logging.getLogger(__name__)


class LinkShowType(models.TextChoices):
    # HJJ: 友情链接展示位置枚举：首页、列表页、文章页、全部、轮播
    I = ('i', _('index'))
    L = ('l', _('list'))
    P = ('p', _('post'))
    A = ('a', _('all'))
    S = ('s', _('slide'))


class BaseModel(models.Model):
    # HJJ: 抽象基类，提供通用字段和基础方法，所有业务模型继承此类
    id = models.AutoField(primary_key=True)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_modify_time = models.DateTimeField(_('modify time'), default=now)

    def save(self, *args, **kwargs):
        # HJJ: 重写save方法，区分普通保存和仅更新浏览量的场景
        is_update_views = isinstance(
            self,
            Article) and 'update_fields' in kwargs and kwargs['update_fields'] == ['views']
        if is_update_views:
            # HJJ: 浏览量自增场景：直接执行update避免触发其他字段更新
            Article.objects.filter(pk=self.pk).update(views=self.views)
        else:
            if 'slug' in self.__dict__:
                # HJJ: 自动根据title或name字段生成URL友好的slug值
                slug = getattr(
                    self, 'title') if 'title' in self.__dict__ else getattr(
                    self, 'name')
                setattr(self, 'slug', slugify(slug))
            super().save(*args, **kwargs)

    def get_full_url(self):
        # HJJ: 获取对象的完整URL（含域名），用于分享和SEO
        site = get_current_site().domain
        url = "https://{site}{path}".format(site=site,
                                            path=self.get_absolute_url())
        return url

    class Meta:
        abstract = True

    @abstractmethod
    def get_absolute_url(self):
        # HJJ: 子类必须实现，返回对象的相对URL路径
        pass


class Article(BaseModel):
    """HJJ: 文章模型，博客核心实体，支持Markdown编辑、多状态管理、分类标签关联"""
    STATUS_CHOICES = (
        ('d', _('Draft')),
        ('p', _('Published')),
    )
    COMMENT_STATUS = (
        ('o', _('Open')),
        ('c', _('Close')),
    )
    TYPE = (
        ('a', _('Article')),
        ('p', _('Page')),
    )
    AI_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('done', _('Done')),
        ('failed', _('Failed')),
        ('stale', _('Stale')),
    )
    title = models.CharField(_('title'), max_length=200, unique=True)
    body = MDTextField(_('body'))
    pub_time = models.DateTimeField(
        _('publish time'), blank=False, null=False, default=now)
    status = models.CharField(
        _('status'),
        max_length=1,
        choices=STATUS_CHOICES,
        default='p')
    comment_status = models.CharField(
        _('comment status'),
        max_length=1,
        choices=COMMENT_STATUS,
        default='o')
    type = models.CharField(_('type'), max_length=1, choices=TYPE, default='a')
    views = models.PositiveIntegerField(_('views'), default=0)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        blank=False,
        null=False,
        on_delete=models.CASCADE)
    article_order = models.IntegerField(
        _('order'), blank=False, null=False, default=0)
    show_toc = models.BooleanField(_('show toc'), blank=False, null=False, default=False)
    category = models.ForeignKey(
        'Category',
        verbose_name=_('category'),
        on_delete=models.CASCADE,
        blank=False,
        null=False)
    tags = models.ManyToManyField('Tag', verbose_name=_('tag'), blank=True)
    # DH: AI 问答生成的文章摘要、要点、受众、关键词及生成状态
    ai_summary = models.TextField(_('ai summary'), blank=True, default='')
    ai_highlights = models.JSONField(
        _('ai highlights'), default=list, blank=True)
    ai_audience = models.TextField(_('ai audience'), blank=True, default='')
    ai_keywords = models.JSONField(_('ai keywords'), default=list, blank=True)
    ai_status = models.CharField(
        _('ai status'),
        max_length=10,
        choices=AI_STATUS_CHOICES,
        default='pending')
    ai_generated_at = models.DateTimeField(
        _('ai generated at'), null=True, blank=True)
    ai_model = models.CharField(
        _('ai model'), max_length=50, blank=True, default='')

    def body_to_string(self):
        # HJJ: 将Markdown正文转为字符串，供全文搜索等场景使用
        return self.body

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-article_order', '-pub_time']
        verbose_name = _('article')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
        indexes = [
            # HJJ: 优化列表查询：type + status + pub_time组合索引
            models.Index(fields=['type', 'status', '-pub_time'], name='idx_type_status_pub'),
            # HJJ: 优化热门文章查询：status + views组合索引
            models.Index(fields=['status', '-views'], name='idx_status_views'),
            # HJJ: 优化作者文章查询：author + status + type组合索引
            models.Index(fields=['author', 'status', 'type'], name='idx_author_status_type'),
            # HJJ: 优化分类查询：category + status组合索引
            models.Index(fields=['category', 'status'], name='idx_category_status'),
        ]

    def get_absolute_url(self):
        # HJJ: 生成文章详情页URL，格式：/article/{year}/{month}/{day}/{id}/
        return reverse('blog:detailbyid', kwargs={
            'article_id': self.id,
            'year': self.creation_time.year,
            'month': self.creation_time.month,
            'day': self.creation_time.day
        })

    @cache_decorator(CacheTimeout.HOUR_10)
    def get_category_tree(self):
        # HJJ: 获取文章所属分类的层级树（从最底层到根），结果缓存10小时
        tree = self.category.get_category_tree()
        names = list(map(lambda c: (c.name, c.get_absolute_url()), tree))
        return names

    def save(self, *args, **kwargs):
        # DH: 仅更新浏览量时直接走父类快捷路径，不触发 AI 内容失效判断
        update_fields = kwargs.get('update_fields')
        if update_fields == ['views']:
            super().save(*args, **kwargs)
            return

        # DH: update_fields 为空时按 Django 约定视为 no-op，不做 stale 判断
        if update_fields is not None and not update_fields:
            super().save(*args, **kwargs)
            return

        # DH: 已生成 AI 内容的文章，标题或正文变化后标记为 stale
        if self.pk and self.ai_status == 'done':
            old_article = Article.objects.filter(pk=self.pk).values(
                'title', 'body').first()
            if old_article and (
                    old_article['title'] != self.title
                    or old_article['body'] != self.body):
                self.ai_status = 'stale'
                # DH: update_fields 未包含 ai_status 时补进去，确保 stale 落库
                if update_fields:
                    update_fields = list(update_fields)
                    if 'ai_status' not in update_fields:
                        update_fields.append('ai_status')
                    kwargs['update_fields'] = update_fields

        # HJJ: 调用父类save，由BaseModel处理slug生成逻辑
        super().save(*args, **kwargs)

    def viewed(self):
        # HJJ: 文章浏览量自增方法，仅更新views字段避免触发其他信号
        self.views += 1
        self.save(update_fields=['views'])

    def comment_list(self):
        # HJJ: 获取文章已启用的评论列表，带缓存机制减少数据库查询
        cache_key = CacheKey.ARTICLE_COMMENTS.format(article_id=self.id)
        value = cache.get(cache_key)
        if value:
            logger.info(f'Cache HIT: article comments (id={self.id})')
            return value
        else:
            comments = self.comment_set.filter(is_enable=True).order_by('-id')
            cache.set(cache_key, comments, CacheTimeout.HOUR_10)
            logger.info(f'Cache MISS: article comments (id={self.id})')
            return comments

    def get_admin_url(self):
        # HJJ: 生成Django后台管理页面的编辑URL
        info = (self._meta.app_label, self._meta.model_name)
        return reverse('admin:%s_%s_change' % info, args=(self.pk,))

    @cache_decorator(expiration=CacheTimeout.HOUR_10)
    def next_article(self):
        # HJJ: 获取下一篇文章（按ID递增），结果缓存10小时
        return Article.objects.filter(
            id__gt=self.id, status='p').order_by('id').first()

    @cache_decorator(expiration=CacheTimeout.HOUR_10)
    def prev_article(self):
        # HJJ: 获取上一篇文章（按ID递减），结果缓存10小时
        return Article.objects.filter(id__lt=self.id, status='p').first()

    def get_first_image_url(self):
        """
        HJJ: 从文章Markdown正文中提取第一张图片的URL
        参数: 无
        返回: str - 图片URL，未找到则返回空字符串
        """
        match = re.search(r'!\[.*?\]\((.+?)\)', self.body)
        if match:
            return match.group(1)
        return ""


class Category(BaseModel):
    """HJJ: 文章分类模型，支持无限极父子分类嵌套"""
    name = models.CharField(_('category name'), max_length=30, unique=True)
    parent_category = models.ForeignKey(
        'self',
        verbose_name=_('parent category'),
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    slug = models.SlugField(default='no-slug', max_length=60, blank=True)
    index = models.IntegerField(default=0, verbose_name=_('index'))

    class Meta:
        ordering = ['-index']
        verbose_name = _('category')
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        # HJJ: 生成分类详情页URL，使用slug而非ID
        return reverse(
            'blog:category_detail', kwargs={
                'category_name': self.slug})

    def __str__(self):
        return self.name

    @cache_decorator(CacheTimeout.HOUR_10)
    def get_category_tree(self):
        """
        HJJ: 递归获取当前分类的所有父级分类链（从自身到根）
        参数: 无
        返回: list[Category] - 按从子到父顺序排列的分类列表
        """
        categorys = []

        def parse(category):
            categorys.append(category)
            if category.parent_category:
                parse(category.parent_category)

        parse(self)
        return categorys

    @cache_decorator(CacheTimeout.HOUR_10)
    def get_sub_categorys(self):
        """
        HJJ: 递归获取当前分类下的所有子分类（含子孙级）
        参数: 无
        返回: list[Category] - 所有后代分类的列表
        """
        categorys = []
        all_categorys = Category.objects.all()

        def parse(category):
            if category not in categorys:
                categorys.append(category)
            childs = all_categorys.filter(parent_category=category)
            for child in childs:
                if category not in categorys:
                    categorys.append(child)
                parse(child)

        parse(self)
        return categorys


class Tag(BaseModel):
    """HJJ: 文章标签模型，与Article为多对多关系"""
    name = models.CharField(_('tag name'), max_length=30, unique=True)
    slug = models.SlugField(default='no-slug', max_length=60, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # HJJ: 生成标签详情页URL，使用slug
        return reverse('blog:tag_detail', kwargs={'tag_name': self.slug})

    @cache_decorator(CacheTimeout.HOUR_10)
    def get_article_count(self):
        # HJJ: 获取该标签下的文章数量（去重），结果缓存10小时
        return Article.objects.filter(tags__name=self.name).distinct().count()

    class Meta:
        ordering = ['name']
        verbose_name = _('tag')
        verbose_name_plural = verbose_name


class Links(models.Model):
    """HJJ: 友情链接模型，支持排序、启用/禁用、按页面类型展示"""
    name = models.CharField(_('link name'), max_length=30, unique=True)
    link = models.URLField(_('link'))
    sequence = models.IntegerField(_('order'), unique=True)
    is_enable = models.BooleanField(
        _('is show'), default=True, blank=False, null=False)
    show_type = models.CharField(
        _('show type'),
        max_length=1,
        choices=LinkShowType.choices,
        default=LinkShowType.I)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_mod_time = models.DateTimeField(_('modify time'), default=now)

    class Meta:
        ordering = ['sequence']
        verbose_name = _('link')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SideBar(models.Model):
    """HJJ: 侧边栏模型，可自定义HTML内容，支持排序和启用控制"""
    name = models.CharField(_('title'), max_length=100)
    content = models.TextField(_('content'))
    sequence = models.IntegerField(_('order'), unique=True)
    is_enable = models.BooleanField(_('is enable'), default=True)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_mod_time = models.DateTimeField(_('modify time'), default=now)

    class Meta:
        ordering = ['sequence']
        verbose_name = _('sidebar')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class BlogSettings(models.Model):
    """HJJ: 博客全局配置模型（单例模式），管理站点信息、主题配色、SEO、统计代码等"""

    COLOR_SCHEMES = (
        ('purple', _('紫色主题 - Purple Dream')),
        ('blue', _('蓝色主题 - Ocean Blue')),
        ('green', _('绿色主题 - Forest Green')),
        ('orange', _('橙色主题 - Sunset Orange')),
        ('pink', _('粉色主题 - Cherry Blossom')),
        ('red', _('红色主题 - Ruby Red')),
        ('indigo', _('靛蓝主题 - Midnight Indigo')),
        ('teal', _('青色主题 - Teal Wave')),
    )

    site_name = models.CharField(
        _('site name'),
        max_length=200,
        null=False,
        blank=False,
        default='')
    site_description = models.TextField(
        _('site description'),
        max_length=1000,
        null=False,
        blank=False,
        default='')
    site_seo_description = models.TextField(
        _('site seo description'), max_length=1000, null=False, blank=False, default='')
    site_keywords = models.TextField(
        _('site keywords'),
        max_length=1000,
        null=False,
        blank=False,
        default='')
    article_sub_length = models.IntegerField(_('article sub length'), default=300)
    sidebar_article_count = models.IntegerField(_('sidebar article count'), default=10)
    sidebar_comment_count = models.IntegerField(_('sidebar comment count'), default=5)
    article_comment_count = models.IntegerField(_('article comment count'), default=5)
    show_google_adsense = models.BooleanField(_('show adsense'), default=False)
    google_adsense_codes = models.TextField(
        _('adsense code'), max_length=2000, null=True, blank=True, default='')
    open_site_comment = models.BooleanField(_('open site comment'), default=True)
    color_scheme = models.CharField(
        _('配色方案'),
        max_length=20,
        choices=COLOR_SCHEMES,
        default='purple',
        help_text=_('选择网站的主题配色方案'))
    global_header = models.TextField("公共头部", null=True, blank=True, default='')
    global_footer = models.TextField("公共尾部", null=True, blank=True, default='')
    beian_code = models.CharField(
        '备案号',
        max_length=2000,
        null=True,
        blank=True,
        default='')
    analytics_code = models.TextField(
        "网站统计代码",
        max_length=1000,
        null=False,
        blank=False,
        default='')
    show_gongan_code = models.BooleanField(
        '是否显示公安备案号', default=False, null=False)
    gongan_beiancode = models.TextField(
        '公安备案号',
        max_length=2000,
        null=True,
        blank=True,
        default='')
    comment_need_review = models.BooleanField(
        '评论是否需要审核', default=False, null=False)

    class Meta:
        verbose_name = _('Website configuration')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.site_name

    def clean(self):
        # HJJ: 校验确保全站只有一条配置记录（单例模式）
        if BlogSettings.objects.exclude(id=self.id).count():
            raise ValidationError(_('There can only be one configuration'))

    def save(self, *args, **kwargs):
        # HJJ: 保存配置后清空全站缓存，使新配置立即生效
        super().save(*args, **kwargs)
        from djangoblog.utils import cache
        cache.clear()