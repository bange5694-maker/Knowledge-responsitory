# XJN: 模块功能：comments 后台管理配置，注册评论与评论表情回应模型，
# XJN: 并提供启用/禁用评论的批量操作及列表页字段跳转链接。
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Comment, CommentReaction


# XJN: 功能：批量禁用所选评论（后台 action）。
# XJN: 入参 modeladmin：当前 ModelAdmin；request：HttpRequest；queryset：被选中的评论集合。
# XJN: 返回值：无（直接批量更新数据库中的 is_enable 字段）。
def disable_commentstatus(modeladmin, request, queryset):
    queryset.update(is_enable=False)


# XJN: 功能：批量启用所选评论（后台 action），常用于审核通过。
# XJN: 入参 modeladmin：当前 ModelAdmin；request：HttpRequest；queryset：被选中的评论集合。
# XJN: 返回值：无（直接批量更新数据库中的 is_enable 字段）。
def enable_commentstatus(modeladmin, request, queryset):
    queryset.update(is_enable=True)


# XJN: 为后台 action 下拉框设置中英文展示名称。
disable_commentstatus.short_description = _('Disable comments')
enable_commentstatus.short_description = _('Enable comments')


# XJN: 评论后台管理类：配置评论列表页展示、筛选、搜索与批量审核操作。
class CommentAdmin(admin.ModelAdmin):
    # XJN: 列表分页大小：每页 20 条。
    list_per_page = 20
    list_display = (
        'id',
        'body',
        'link_to_userinfo',
        'link_to_article',
        'is_enable',
        'creation_time')
    list_display_links = ('id', 'body', 'is_enable')
    list_filter = ('is_enable',)
    # XJN: 创建/修改时间由系统自动维护，后台表单中不展示，避免手工篡改。
    exclude = ('creation_time', 'last_modify_time')
    # XJN: 注册批量启用/禁用评论的操作。
    actions = [disable_commentstatus, enable_commentstatus]
    raw_id_fields = ('author', 'article')
    search_fields = ('body',)

    # XJN: 功能：在评论列表页生成指向评论作者的超链接。
    # XJN: 入参 obj：当前 Comment 实例。
    # XJN: 返回值：安全转义后的 HTML 链接（作者昵称，缺失时回退为邮箱）。
    def link_to_userinfo(self, obj):
        info = (obj.author._meta.app_label, obj.author._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.author.id,))
        return format_html(
            u'<a href="%s">%s</a>' %
            (link, obj.author.nickname if obj.author.nickname else obj.author.email))

    # XJN: 功能：在评论列表页生成指向所属文章的后台编辑链接。
    # XJN: 入参 obj：当前 Comment 实例。
    # XJN: 返回值：安全转义后的 HTML 链接（文章标题）。
    def link_to_article(self, obj):
        info = (obj.article._meta.app_label, obj.article._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.article.id,))
        return format_html(
            u'<a href="%s">%s</a>' % (link, obj.article.title))

    link_to_userinfo.short_description = _('User')
    link_to_article.short_description = _('Article')


class CommentReactionAdmin(admin.ModelAdmin):
    # XJN: 表情回应后台管理类：展示回应类型、关联评论与用户，支持按类型/时间筛选与搜索。
    list_display = ('id', 'reaction_type', 'link_to_comment', 'link_to_user', 'created_at')
    list_display_links = ('id', 'reaction_type')
    list_filter = ('reaction_type', 'created_at')
    raw_id_fields = ('comment', 'user')
    search_fields = ('comment__body', 'user__username')
    date_hierarchy = 'created_at'

    # XJN: 功能：在表情回应列表页生成指向被回应评论的后台链接。
    # XJN: 入参 obj：当前 CommentReaction 实例。
    # XJN: 返回值：安全转义后的 HTML 链接，显示为 Comment #评论ID。
    def link_to_comment(self, obj):
        info = (obj.comment._meta.app_label, obj.comment._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.comment.id,))
        return format_html(
            u'<a href="%s">Comment #%s</a>' % (link, obj.comment.id))

    # XJN: 功能：在表情回应列表页生成指向回应用户的后台链接。
    # XJN: 入参 obj：当前 CommentReaction 实例。
    # XJN: 返回值：安全转义后的 HTML 链接（用户昵称，缺失时回退为用户名）。
    def link_to_user(self, obj):
        info = (obj.user._meta.app_label, obj.user._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.user.id,))
        return format_html(
            u'<a href="%s">%s</a>' %
            (link, obj.user.nickname if obj.user.nickname else obj.user.username))

    link_to_comment.short_description = _('Comment')
    link_to_user.short_description = _('User')


# XJN: 将评论与表情回应模型注册到 Django 后台管理站点。
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentReaction, CommentReactionAdmin)
