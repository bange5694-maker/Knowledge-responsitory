# DH: 这个文件把 Django 自带的后台操作日志接进我们的后台，能看谁在什么时候改了什么。

from django.contrib import admin
from django.contrib.admin.models import DELETION
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse, NoReverseMatch
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


# DH: 操作日志的管理页面。
class LogEntryAdmin(admin.ModelAdmin):
    # DH: 可以按对象类型筛选。
    list_filter = [
        'content_type'
    ]

    # DH: 可以按对象名和修改内容搜索。
    search_fields = [
        'object_repr',
        'change_message'
    ]

    # DH: 列表里显示时间、操作人、对象、修改内容这些列。
    list_display_links = [
        'action_time',
        'get_change_message',
    ]
    list_display = [
        'action_time',
        'user_link',
        'content_type',
        'object_link',
        'get_change_message',
    ]

    # DH: 日志是系统自动记的，不允许手动添加。
    def has_add_permission(self, request):
        return False

    # DH: 只有超级管理员或专门有权限的人能看，而且只能看不能提交修改。
    def has_change_permission(self, request, obj=None):
        return (
                request.user.is_superuser or
                request.user.has_perm('admin.change_logentry')
        ) and request.method != 'POST'

    # DH: 日志不让删，方便以后查问题。
    def has_delete_permission(self, request, obj=None):
        return False

    # DH: 把被操作的对象变成能点的链接，点进去就是那条记录的编辑页。
    def object_link(self, obj):
        object_link = escape(obj.object_repr)
        content_type = obj.content_type

        if obj.action_flag != DELETION and content_type is not None:
            # try returning an actual link instead of object repr string
            try:
                url = reverse(
                    'admin:{}_{}_change'.format(content_type.app_label,
                                                content_type.model),
                    args=[obj.object_id]
                )
                object_link = '<a href="{}">{}</a>'.format(url, object_link)
            except NoReverseMatch:
                # DH: 对象已经被删了的话链接会失败，这里直接跳过，不报错。
                pass
        # DH: 上面拼的是 HTML，要告诉模板这段可以直接显示。
        return mark_safe(object_link)

    object_link.admin_order_field = 'object_repr'
    object_link.short_description = _('object')

    # DH: 操作人也做成链接，点进去是他的用户页。
    def user_link(self, obj):
        content_type = ContentType.objects.get_for_model(type(obj.user))
        user_link = escape(force_str(obj.user))
        try:
            # try returning an actual link instead of object repr string
            url = reverse(
                'admin:{}_{}_change'.format(content_type.app_label,
                                            content_type.model),
                args=[obj.user.pk]
            )
            user_link = '<a href="{}">{}</a>'.format(url, user_link)
        except NoReverseMatch:
            pass
        return mark_safe(user_link)

    user_link.admin_order_field = 'user'
    user_link.short_description = _('user')

    # DH: 顺手把对象类型一起查出来，避免列表里每行再查一次数据库。
    def get_queryset(self, request):
        queryset = super(LogEntryAdmin, self).get_queryset(request)
        return queryset.prefetch_related('content_type')

    # DH: 把“批量删除”这个操作去掉，日志不能批量删。
    def get_actions(self, request):
        actions = super(LogEntryAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
