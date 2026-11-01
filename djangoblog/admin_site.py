# DH: 这个文件是后台管理站点的“总装配”：新建一个后台站点，再把各个表的管理页面挂上去。

from django.contrib.admin import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site

# DH: 把各个应用的后台管理类都导入进来，下面注册的时候要用。
from accounts.admin import *
from blog.admin import *
from blog.models import *
from comments.admin import *
from comments.models import *
from djangoblog.logentryadmin import LogEntryAdmin
from oauth.admin import *
from oauth.models import *
from servermanager.admin import *
from servermanager.models import *


# DH: 自定义的后台站点，标题换成自己的，登录权限也自己控制。
class DjangoBlogAdminSite(AdminSite):
    # DH: 后台顶部和浏览器标题显示的文字。
    site_header = 'djangoblog administration'
    site_title = 'djangoblog site admin'

    # DH: 初始化时把站点名字传进去，默认叫 admin。
    def __init__(self, name='admin'):
        super().__init__(name)

    # DH: 只有超级管理员才能进这个后台，普通管理员也不行。
    def has_permission(self, request):
        return request.user.is_superuser

    # DH: 下面这段被注释掉了，是以前留的刷新缓存入口，暂时用不上。
    # def get_urls(self):
    #     urls = super().get_urls()
    #     from django.urls import path
    #     from blog.views import refresh_memcache
    #
    #     my_urls = [
    #         path('refresh/', self.admin_view(refresh_memcache), name="refresh"),
    #     ]
    #     return urls + my_urls


# DH: 真正创建后台站点对象，后面都用它来注册。
admin_site = DjangoBlogAdminSite(name='admin')

# DH: 文章、分类、标签、友链、侧边栏、站点设置。
admin_site.register(Article, ArticlelAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(Links, LinksAdmin)
admin_site.register(SideBar, SideBarAdmin)
admin_site.register(BlogSettings, BlogSettingsAdmin)

# DH: 后台命令和邮件发送日志。
admin_site.register(commands, CommandsAdmin)
admin_site.register(EmailSendLog, EmailSendLogAdmin)

# DH: 用户管理。
admin_site.register(BlogUser, BlogUserAdmin)

# DH: 评论管理。
admin_site.register(Comment, CommentAdmin)

# DH: 第三方账号和第三方登录配置。
admin_site.register(OAuthUser, OAuthUserAdmin)
admin_site.register(OAuthConfig, OAuthConfigAdmin)

# DH: 站点域名设置。
admin_site.register(Site, SiteAdmin)

# DH: 操作日志。
admin_site.register(LogEntry, LogEntryAdmin)
