# HJJ: 博客后台管理模块，注册各模型到Django Admin，
# HJJ: 提供批量操作（发布/草稿/开关评论）、自定义表单、单例配置管理等增强功能

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Register your models here.
from .models import Article, Category, Tag, Links, SideBar, BlogSettings


class ArticleForm(forms.ModelForm):
    # HJJ: 文章编辑表单，预留AdminPagedownWidget集成点（当前注释）
    # body = forms.CharField(widget=AdminPagedownWidget())

    class Meta:
        model = Article
        fields = '__all__'


def makr_article_publish(modeladmin, request, queryset):
    # HJJ: 批量操作 - 将选中文章设为已发布状态
    queryset.update(status='p')


def draft_article(modeladmin, request, queryset):
    # HJJ: 批量操作 - 将选中文章设为草稿状态
    queryset.update(status='d')


def close_article_commentstatus(modeladmin, request, queryset):
    # HJJ: 批量操作 - 关闭选中文章的评论功能
    queryset.update(comment_status='c')


def open_article_commentstatus(modeladmin, request, queryset):
    # HJJ: 批量操作 - 开启选中文章的评论功能
    queryset.update(comment_status='o')


makr_article_publish.short_description = _('Publish selected articles')
draft_article.short_description = _('Draft selected articles')
close_article_commentstatus.short_description = _('Close article comments')
open_article_commentstatus.short_description = _('Open article comments')


class ArticlelAdmin(admin.ModelAdmin):
    # HJJ: 文章管理配置，每页20条，支持标题和正文搜索
    list_per_page = 20
    search_fields = ('body', 'title')
    form = ArticleForm
    list_display = (
        'id',
        'title',
        'author',
        'link_to_category',
        'creation_time',
        'views',
        'status',
        'type',
        'article_order')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'type', 'category')
    date_hierarchy = 'creation_time'
    filter_horizontal = ('tags',)
    exclude = ('creation_time', 'last_modify_time')
    view_on_site = True
    actions = [
        makr_article_publish,
        draft_article,
        close_article_commentstatus,
        open_article_commentstatus]
    raw_id_fields = ('author', 'category',)

    def link_to_category(self, obj):
        # HJJ: 自定义列 - 将分类名渲染为可点击的后台编辑链接
        info = (obj.category._meta.app_label, obj.category._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.category.id,))
        return format_html(u'<a href="%s">%s</a>' % (link, obj.category.name))

    link_to_category.short_description = _('category')

    def get_form(self, request, obj=None, **kwargs):
        # HJJ: 限制作者字段可选范围为超级管理员用户
        form = super(ArticlelAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['author'].queryset = get_user_model(
        ).objects.filter(is_superuser=True)
        return form

    def save_model(self, request, obj, form, change):
        # HJJ: 保存文章时调用父类默认行为（保留扩展点）
        super(ArticlelAdmin, self).save_model(request, obj, form, change)

    def get_view_on_site_url(self, obj=None):
        # HJJ: 生成前台查看链接，优先使用对象完整URL，否则返回站点域名
        if obj:
            url = obj.get_full_url()
            return url
        else:
            from djangoblog.utils import get_current_site
            site = get_current_site().domain
            return site


class TagAdmin(admin.ModelAdmin):
    # HJJ: 标签管理，隐藏slug和时间戳字段（自动生成）
    exclude = ('slug', 'last_mod_time', 'creation_time')


class CategoryAdmin(admin.ModelAdmin):
    # HJJ: 分类管理，显示名称、父分类、排序索引
    list_display = ('name', 'parent_category', 'index')
    exclude = ('slug', 'last_mod_time', 'creation_time')


class LinksAdmin(admin.ModelAdmin):
    # HJJ: 友情链接管理，隐藏时间戳字段
    exclude = ('last_mod_time', 'creation_time')


class SideBarAdmin(admin.ModelAdmin):
    # HJJ: 侧边栏管理，显示名称、内容、启用状态、排序
    list_display = ('name', 'content', 'is_enable', 'sequence')
    exclude = ('last_mod_time', 'creation_time')


class BlogSettingsAdmin(admin.ModelAdmin):
    """HJJ: 单例配置Admin - 直接跳转到编辑页面，防止重复创建和误删"""

    def has_add_permission(self, request):
        # HJJ: 如果已经存在配置，则禁止添加新配置（单例约束）
        return not BlogSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # HJJ: 禁止删除配置，防止系统关键配置丢失
        return False

    def changelist_view(self, request, extra_context=None):
        # HJJ: 覆盖列表视图，直接重定向到编辑页面，提升用户体验
        from django.http import HttpResponseRedirect
        obj = BlogSettings.objects.first()
        if obj:
            return HttpResponseRedirect(
                reverse('admin:blog_blogsettings_change', args=[obj.pk])
            )
        # HJJ: 如果不存在配置，跳转到添加页面
        return HttpResponseRedirect(
            reverse('admin:blog_blogsettings_add')
        )

    def save_model(self, request, obj, form, change):
        # HJJ: 保存设置时清除全站缓存，确保新配置立即生效
        super().save_model(request, obj, form, change)
        from djangoblog.utils import cache
        cache.clear()
        self.message_user(request, '设置已保存，缓存已清除')