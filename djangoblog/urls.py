# DH: 这个文件是网站的总路由表，把各个网址分给对应的应用去处理。

"""djangoblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.urls import re_path
from haystack.views import search_view_factory
from django.http import JsonResponse
import time

from blog.views import EsSearchView
from djangoblog.admin_site import admin_site
from djangoblog.elasticsearch_backend import ElasticSearchModelSearchForm
from djangoblog.feeds import DjangoBlogFeed
from djangoblog.sitemap import ArticleSiteMap, CategorySiteMap, StaticViewSitemap, TagSiteMap, UserSiteMap

# DH: 站点地图里要包含哪些内容：文章、分类、标签、作者和几个固定页面。
sitemaps = {

    'blog': ArticleSiteMap,
    'Category': CategorySiteMap,
    'Tag': TagSiteMap,
    'User': UserSiteMap,
    'static': StaticViewSitemap
}

# DH: 出 404、500、403 错误时，分别用 blog 应用里的哪个页面来显示。
handler404 = 'blog.views.page_not_found_view'
handler500 = 'blog.views.server_error_view'
handle403 = 'blog.views.permission_denied_view'


# DH: 健康检查接口，访问 /health/ 会返回一个“healthy”，给监控或部署脚本确认服务还活着。
def health_check(request):
    """
    健康检查接口
    简单返回服务健康状态
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time()
    })

urlpatterns = [
    # DH: 多语言相关的路由。
    path('i18n/', include('django.conf.urls.i18n')),
    # DH: 健康检查路由。
    path('health/', health_check, name='health_check'),
]
urlpatterns += i18n_patterns(
    # DH: 后台管理站点，管理员在这里维护数据。
    re_path(r'^admin/', admin_site.urls),
    # DH: 博客前台的路由（首页、文章、分类等）。
    re_path(r'', include('blog.urls', namespace='blog')),
    # DH: Markdown 编辑器的上传等接口。
    re_path(r'mdeditor/', include('mdeditor.urls')),
    # DH: 评论相关的路由。
    re_path(r'', include('comments.urls', namespace='comment')),
    # DH: 账户相关的路由（注册、登录、找回密码）。
    re_path(r'', include('accounts.urls', namespace='account')),
    # DH: 第三方登录相关的路由。
    re_path(r'', include('oauth.urls', namespace='oauth')),
    # DH: 站点地图，给搜索引擎看网站有哪些页面。
    re_path(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
            name='django.contrib.sitemaps.views.sitemap'),
    # DH: RSS 订阅地址。
    re_path(r'^feed/$', DjangoBlogFeed()),
    re_path(r'^rss/$', DjangoBlogFeed()),
    # DH: 站内搜索，用 Haystack 的搜索页面。
    re_path('^search', search_view_factory(view_class=EsSearchView, form_class=ElasticSearchModelSearchForm),
            name='search'),
    # DH: 微信机器人等后台服务的路由。
    re_path(r'', include('servermanager.urls', namespace='servermanager'))
    , prefix_default_language=False) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# DH: 开发模式下，让 Django 直接提供上传的文件，正式环境一般交给 Nginx。
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
