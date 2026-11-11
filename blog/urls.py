# HJJ: 博客URL路由配置模块，定义所有URL模式与视图函数的映射关系，
# HJJ: 包含文章列表/详情、分类/标签/作者归档、搜索、文件上传等路由

from django.urls import path
from django.views.decorators.cache import cache_page

from . import views

app_name = "blog"
urlpatterns = [
    # HJJ: 首页路由 - 不带页码时默认显示第1页
    path(
        r'',
        views.IndexView.as_view(),
        name='index'),
    
    # HJJ: 首页分页路由 - 支持指定页码
    path(
        r'page/<int:page>/',
        views.IndexView.as_view(),
        name='index_page'),
    
    # HJJ: 文章详情页路由 - 使用年/月/日/ID的SEO友好格式
    # 例如: /article/2024/01/15/123.html
    path(
        r'article/<int:year>/<int:month>/<int:day>/<int:article_id>.html',
        views.ArticleDetailView.as_view(),
        name='detailbyid'),
    
    # HJJ: 分类列表路由 - 使用slug作为URL标识
    # 例如: /category/python.html
    path(
        r'category/<slug:category_name>.html',
        views.CategoryDetailView.as_view(),
        name='category_detail'),
    
    # HJJ: 分类列表分页路由 - 支持分页浏览
    # 例如: /category/python/2.html
    path(
        r'category/<slug:category_name>/<int:page>.html',
        views.CategoryDetailView.as_view(),
        name='category_detail_page'),
    
    # HJJ: 作者文章列表路由 - 按用户名过滤
    # 例如: /author/admin.html
    path(
        r'author/<author_name>.html',
        views.AuthorDetailView.as_view(),
        name='author_detail'),
    
    # HJJ: 作者文章列表分页路由
    # 例如: /author/admin/2.html
    path(
        r'author/<author_name>/<int:page>.html',
        views.AuthorDetailView.as_view(),
        name='author_detail_page'),
    
    # HJJ: 标签文章列表路由 - 使用slug作为URL标识
    # 例如: /tag/django.html
    path(
        r'tag/<slug:tag_name>.html',
        views.TagDetailView.as_view(),
        name='tag_detail'),
    
    # HJJ: 标签文章列表分页路由
    # 例如: /tag/django/2.html
    path(
        r'tag/<slug:tag_name>/<int:page>.html',
        views.TagDetailView.as_view(),
        name='tag_detail_page'),
    
    # HJJ: 文章归档页面路由 - 使用cache_page装饰器缓存1小时
    # 例如: /archives.html
    path(
        'archives.html',
        cache_page(
            60 * 60)(
            views.ArchivesView.as_view()),
        name='archives'),
    
    # HJJ: 友情链接页面路由
    # 例如: /links.html
    path(
        'links.html',
        views.LinkListView.as_view(),
        name='links'),
    
    # HJJ: 文件上传接口路由（图床功能）
    # 例如: /upload
    path(
        r'upload',
        views.fileupload,
        name='upload'),
    
    # HJJ: 清理缓存接口路由（管理员维护用）
    # 例如: /clean
    path(
        r'clean',
        views.clean_cache_view,
        name='clean'),
]