# LZH: 模块功能：servermanager 应用的 Django 后台注册，提供命令配置与邮件发送日志的管理界面。

from django.contrib import admin
# Register your models here.


# LZH: 命令后台：列表页展示命令标题、命令内容与描述，支持增删改查。
class CommandsAdmin(admin.ModelAdmin):
    list_display = ('title', 'command', 'describe')


# LZH: 邮件日志后台：列表页展示标题、收件人、发送结果与时间；全部字段只读且禁止新增，
# LZH: 保证日志只能由系统写入，避免人工篡改审计记录。
class EmailSendLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'emailto', 'send_result', 'creation_time')
    readonly_fields = (
        'title',
        'emailto',
        'send_result',
        'creation_time',
        'content')

    # LZH: 方法说明：重写新增权限判断，返回 False 表示后台不允许手工新增日志记录。
    # LZH: 参数：request（当前请求）；返回：bool，恒为 False。
    def has_add_permission(self, request):
        return False
