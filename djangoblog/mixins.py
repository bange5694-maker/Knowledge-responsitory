#!/usr/bin/env python
# encoding: utf-8
# DH: 这个文件放一些“混入类”，把重复的代码抽出来，别的类继承一下就有这些功能。

"""
Django Blog 混入类 (Mixins)
提供可复用的功能模块，减少代码重复
"""

import logging
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# ===== 模型层 Mixin =====

# DH: 给模型加创建时间和修改时间，省得每个表都写一遍。
class TimeStampedModel(models.Model):
    """
    抽象模型：为所有模型提供统一的时间戳字段

    提供 created_at 和 updated_at 字段，自动管理时间戳
    继承此模型可以消除重复的时间字段定义

    Usage:
        class MyModel(TimeStampedModel):
            name = models.CharField(max_length=100)
    """
    created_at = models.DateTimeField(
        _('creation time'),
        default=now,
        db_index=True,
        help_text=_('The date and time when this object was created')
    )
    updated_at = models.DateTimeField(
        _('last modify time'),
        default=now,
        help_text=_('The date and time when this object was last modified')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    # DH: 保存时自动把修改时间更新成现在；如果只更新部分字段，也要把修改时间带上。
    def save(self, *args, **kwargs):
        """
        重写 save 方法，自动更新 updated_at 字段

        注意：如果使用 update_fields 参数，需要明确包含 updated_at
        """
        # 检查是否是部分更新（指定了 update_fields）
        update_fields = kwargs.get('update_fields')
        if update_fields:
            # 如果指定了 update_fields 但不包含 updated_at，则添加它
            if 'updated_at' not in update_fields:
                update_fields = list(update_fields) + ['updated_at']
                kwargs['update_fields'] = update_fields

        # 更新时间戳
        self.updated_at = now()

        super().save(*args, **kwargs)


# ===== 视图层 Mixin =====

# DH: 同一个请求里多次用同一个 slug 查对象时，只查一次数据库，后面直接用上次查到的。
class SlugCachedMixin:
    """
    Mixin: 缓存 slug 查询结果，避免重复数据库查询

    在同一个请求周期内，多次获取同一个 slug 对应的对象时，
    只会执行一次数据库查询，后续调用会使用缓存的对象

    Attributes:
        slug_url_kwarg: URL 参数名，默认为 'slug'
        slug_model: 要查询的模型类

    Usage:
        class MyView(SlugCachedMixin, ListView):
            slug_url_kwarg = 'category_slug'
            slug_model = Category

            def get_queryset(self):
                category = self.get_slug_object()
                return Article.objects.filter(category=category)
    """
    slug_url_kwarg = 'slug'
    slug_model = None

    # DH: 第一次查的时候存起来，后面再调用就不查库了；查不到就返回 404。
    def get_slug_object(self):
        """
        获取并缓存 slug 对应的对象

        Returns:
            Model instance: slug 对应的模型实例

        Raises:
            Http404: 如果 slug 对应的对象不存在
        """
        if not hasattr(self, '_slug_object'):
            if self.slug_model is None:
                raise ValueError(
                    f'{self.__class__.__name__} must define slug_model attribute'
                )

            slug = self.kwargs.get(self.slug_url_kwarg)
            self._slug_object = get_object_or_404(self.slug_model, slug=slug)
            logger.debug(
                f'Loaded {self.slug_model.__name__} object: {self._slug_object} (slug={slug})'
            )

        return self._slug_object


# DH: 查文章时把作者、分类、标签一起查出来，避免列表里每篇文章再单独查一次数据库。
class OptimizedArticleQueryMixin:
    """
    Mixin: 优化文章查询（预加载关联对象）

    使用 select_related 和 prefetch_related 优化文章查询，
    减少数据库查询次数，避免 N+1 查询问题

    Usage:
        class MyView(OptimizedArticleQueryMixin, ListView):
            def get_queryset(self):
                return self.get_optimized_article_queryset().filter(status='p')
    """

    def get_optimized_article_queryset(self):
        """
        返回优化后的 Article queryset

        使用 select_related 预加载外键关联：
            - author: 文章作者
            - category: 文章分类

        使用 prefetch_related 预加载多对多关联：
            - tags: 文章标签

        Returns:
            QuerySet: 优化后的 Article queryset
        """
        from blog.models import Article

        return Article.objects.select_related(
            'author',      # 预加载作者（ForeignKey）
            'category'     # 预加载分类（ForeignKey）
        ).prefetch_related(
            'tags'         # 预加载标签（ManyToMany）
        )


# DH: 给列表页加缓存：先看缓存里有没有，没有再查数据库并存进去。
class CachedListViewMixin:
    """
    Mixin: 为 ListView 提供统一的缓存逻辑

    自动缓存 queryset 结果，减少数据库查询
    子类需要实现 get_queryset_cache_key() 和 get_queryset_data() 方法

    Usage:
        class MyView(CachedListViewMixin, ListView):
            def get_queryset_cache_key(self):
                return f'my_list_{self.page_number}'

            def get_queryset_data(self):
                return Article.objects.filter(status='p')
    """

    # DH: 下面两个方法让子类自己写：一个给缓存键，一个给真正要查的数据。
    def get_queryset_cache_key(self):
        """
        子类实现：返回缓存 key

        Returns:
            str: 缓存键

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} must implement get_queryset_cache_key()'
        )

    def get_queryset_data(self):
        """
        子类实现：返回实际数据

        Returns:
            QuerySet: 要缓存的 queryset

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError(
            f'{self.__class__.__name__} must implement get_queryset_data()'
        )

    # DH: 有缓存就直接返回，没有就查库并写缓存。
    def get_queryset_from_cache(self, cache_key):
        """
        从缓存获取 queryset，如果缓存不存在则查询并缓存

        Args:
            cache_key: 缓存键

        Returns:
            QuerySet: 查询结果
        """
        from djangoblog.utils import cache

        value = cache.get(cache_key)
        if value:
            logger.info(f'Cache HIT: {cache_key}')
            return value

        queryset = self.get_queryset_data()
        cache.set(cache_key, queryset)
        logger.info(f'Cache MISS: {cache_key}')
        return queryset

    # DH: 列表页真正取数据的时候走这里，自动套上缓存。
    def get_queryset(self):
        """
        重写 get_queryset，使用缓存

        Returns:
            QuerySet: 查询结果（从缓存或数据库）
        """
        key = self.get_queryset_cache_key()
        return self.get_queryset_from_cache(key)


# DH: 从地址或参数里取页码，取不到或者不是数字就按第 1 页算。
class PageNumberMixin:
    """
    Mixin: 提供页码获取功能

    从 URL 参数或 GET 参数中获取当前页码

    Usage:
        class MyView(PageNumberMixin, ListView):
            def get_queryset_cache_key(self):
                return f'list_{self.page_number}'
    """
    page_kwarg = 'page'

    @property
    def page_number(self):
        """
        获取当前页码

        从 URL kwargs 或 GET 参数中获取页码，默认为 1

        Returns:
            int: 当前页码
        """
        page = self.kwargs.get(self.page_kwarg) or \
               self.request.GET.get(self.page_kwarg) or 1

        try:
            return int(page)
        except (ValueError, TypeError):
            return 1


# DH: 把上面几个混在一起，文章列表页继承它就有查询优化、缓存和页码功能。
class ArticleListMixin(
    OptimizedArticleQueryMixin,
    CachedListViewMixin,
    PageNumberMixin
):
    """
    Mixin: 组合多个 Mixin，提供完整的文章列表功能

    继承此 Mixin 的视图自动具备：
    - 优化的文章查询
    - 缓存支持
    - 页码处理

    Usage:
        class MyArticleListView(ArticleListMixin, ListView):
            def get_queryset_data(self):
                return self.get_optimized_article_queryset().filter(status='p')

            def get_queryset_cache_key(self):
                return f'my_list_{self.page_number}'
    """
    pass
