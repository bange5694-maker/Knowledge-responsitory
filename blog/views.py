# HJJ: 博客视图模块，包含文章列表/详情、分类/标签/作者归档、搜索、文件上传等所有核心视图，
# HJJ: 采用Mixin模式优化查询性能、实现缓存策略和SEO数据注入

import logging
import os
import uuid

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from haystack.views import SearchView

from blog.models import Article, Category, LinkShowType, Links, Tag
from comments.forms import CommentForm
from djangoblog.plugin_manage import hooks
from djangoblog.plugin_manage.hook_constants import ARTICLE_CONTENT_HOOK_NAME
from djangoblog.utils import cache, get_blog_setting, get_sha256
from djangoblog.mixins import (
    SlugCachedMixin,
    ArticleListMixin,
    OptimizedArticleQueryMixin,
    CachedListViewMixin,
    PageNumberMixin
)

logger = logging.getLogger(__name__)


class ArticleListView(CachedListViewMixin, PageNumberMixin, ListView):
    """
    HJJ: 文章列表视图基类（重构版）
    使用 Mixin 简化代码，消除重复逻辑
    子类只需实现 get_queryset_data() 和 get_queryset_cache_key() 方法
    """
    # HJJ: 指定渲染模板
    template_name = 'blog/article_index.html'
    # HJJ: 模板中使用的上下文变量名
    context_object_name = 'article_list'
    # HJJ: 页面类型标识，子类覆盖
    page_type = ''
    # HJJ: 每页文章数，从settings读取
    paginate_by = settings.PAGINATE_BY
    # HJJ: URL中分页参数名
    page_kwarg = 'page'
    # HJJ: 友情链接展示类型，默认为列表页
    link_type = LinkShowType.L

    def get_view_cache_key(self):
        # HJJ: 获取视图缓存键，基于请求页码
        return self.request.get['pages']

    def get_context_data(self, **kwargs):
        # HJJ: 向模板传递友情链接类型
        kwargs['linktype'] = self.link_type
        return super(ArticleListView, self).get_context_data(**kwargs)


class IndexView(OptimizedArticleQueryMixin, ArticleListView):
    """
    HJJ: 首页视图（重构版）
    继承 OptimizedArticleQueryMixin 获得优化的查询方法
    """
    # HJJ: 首页友情链接类型为首页
    link_type = LinkShowType.I

    def get_queryset_data(self):
        # HJJ: 使用Mixin提供的优化查询方法，筛选已发布的文章类型
        return self.get_optimized_article_queryset().filter(
            type='a', status='p'
        )

    def get_queryset_cache_key(self):
        # HJJ: 首页缓存键基于页码
        return f'index_{self.page_number}'

    def get_context_data(self, **kwargs):
        # HJJ: 注入首页SEO元数据
        context = super().get_context_data(**kwargs)
        blog_setting = get_blog_setting()
        context['seo_title'] = f"{blog_setting.site_name} | {blog_setting.site_description}"
        context['seo_description'] = blog_setting.site_seo_description
        context['seo_keywords'] = blog_setting.site_keywords
        return context


class ArticleDetailView(DetailView):
    '''
    HJJ: 文章详情页面视图
    处理文章展示、评论分页、上下篇文章导航、SEO数据、插件钩子触发
    '''
    template_name = 'blog/article_detail.html'
    model = Article
    pk_url_kwarg = 'article_id'
    context_object_name = "article"

    def get_context_data(self, **kwargs):
        # HJJ: 初始化评论表单
        comment_form = CommentForm()

        # HJJ: 优化查询：使用select_related和prefetch_related减少N+1查询
        from comments.models import Comment
        parent_comments = Comment.objects.filter(
            article=self.object,
            parent_comment=None,
            is_enable=True
        ).select_related('author').prefetch_related(
            'comment_set__author'  # HJJ: 预加载子评论及其作者
        ).order_by('-id')

        # HJJ: 获取所有评论（带缓存）
        article_comments = self.object.comment_list()

        # HJJ: 评论分页逻辑
        blog_setting = get_blog_setting()
        paginator = Paginator(parent_comments, blog_setting.article_comment_count)
        page = self.request.GET.get('comment_page', '1')
        if not page.isnumeric():
            page = 1
        else:
            page = int(page)
            if page < 1:
                page = 1
            if page > paginator.num_pages:
                page = paginator.num_pages

        p_comments = paginator.page(page)
        next_page = p_comments.next_page_number() if p_comments.has_next() else None
        prev_page = p_comments.previous_page_number() if p_comments.has_previous() else None

        # HJJ: 生成上下页锚点链接
        if next_page:
            kwargs[
                'comment_next_page_url'] = self.object.get_absolute_url() + f'?comment_page={next_page}#commentlist-container'
        if prev_page:
            kwargs[
                'comment_prev_page_url'] = self.object.get_absolute_url() + f'?comment_page={prev_page}#commentlist-container'
        kwargs['form'] = comment_form
        kwargs['article_comments'] = article_comments
        kwargs['p_comments'] = p_comments
        kwargs['comment_count'] = len(
            article_comments) if article_comments else 0

        # HJJ: 上下篇文章导航（带缓存）
        kwargs['next_article'] = self.object.next_article
        kwargs['prev_article'] = self.object.prev_article

        context = super(ArticleDetailView, self).get_context_data(**kwargs)
        article = self.object
        
        # HJJ: SEO数据处理：Markdown转纯文本截取描述
        blog_setting = get_blog_setting()
        from django.utils.html import strip_tags
        from django.utils.text import Truncator
        from djangoblog.utils import CommonMarkdown
        
        # HJJ: Markdown -> HTML -> 纯文本，彻底去除格式
        html_content = CommonMarkdown.get_markdown(article.body)
        description = strip_tags(html_content)
        description = ' '.join(description.split())  # HJJ: 规范化空白字符
        description = Truncator(description).chars(150, truncate='...')
        
        # HJJ: 关键词处理：使用文章标签，若无则用站点默认关键词
        tags = [tag.name.strip() for tag in article.tags.all()]
        keywords = ", ".join(tags) if tags else blog_setting.site_keywords
        
        context['seo_title'] = f"{article.title} | {blog_setting.site_name}"
        context['seo_description'] = description
        context['seo_keywords'] = keywords
        
        # HJJ: 触发文章详情加载钩子，让插件可以添加额外上下文数据
        from djangoblog.plugin_manage.hook_constants import ARTICLE_DETAIL_LOAD
        hooks.run_action(ARTICLE_DETAIL_LOAD, article=article, context=context, request=self.request)
        
        # HJJ: Action Hook，通知插件"文章详情已获取"
        hooks.run_action('after_article_body_get', article=article, request=self.request)
        return context


class CategoryDetailView(SlugCachedMixin, OptimizedArticleQueryMixin, ArticleListView):
    """
    HJJ: 分类目录列表视图（重构版）
    使用 SlugCachedMixin 避免重复查询 Category
    使用 OptimizedArticleQueryMixin 优化文章查询
    """
    page_type = "分类目录归档"
    slug_url_kwarg = 'category_name'
    slug_model = Category

    def get_queryset_data(self):
        # HJJ: 使用Mixin缓存的对象，只查询一次Category
        category = self.get_slug_object()
        # HJJ: 获取该分类及其所有子分类的名称列表
        categorynames = [c.name for c in category.get_sub_categorys()]

        return self.get_optimized_article_queryset().filter(
            category__name__in=categorynames, status='p'
        )

    def get_queryset_cache_key(self):
        # HJJ: 复用缓存的对象，不再重复查询数据库
        category = self.get_slug_object()
        return f'category_list_{category.name}_{self.page_number}'

    def get_context_data(self, **kwargs):
        category = self.get_slug_object()
        categoryname = category.name

        try:
            categoryname = categoryname.split('/')[-1]
        except BaseException:
            pass

        kwargs['page_type'] = CategoryDetailView.page_type
        kwargs['tag_name'] = categoryname
        
        # HJJ: 注入分类页SEO元数据
        blog_setting = get_blog_setting()
        article_count = self.get_queryset().count()
        kwargs['seo_title'] = f"{categoryname} | {blog_setting.site_name}"
        kwargs['seo_description'] = f"浏览 {categoryname} 分类下的所有文章，共 {article_count} 篇文章。"
        kwargs['seo_keywords'] = f"{categoryname}, {blog_setting.site_keywords}"
        
        return super(CategoryDetailView, self).get_context_data(**kwargs)


class AuthorDetailView(OptimizedArticleQueryMixin, ArticleListView):
    """
    HJJ: 作者详情页视图（重构版）
    使用 OptimizedArticleQueryMixin 优化文章查询
    """
    page_type = '作者文章归档'

    def get_queryset_cache_key(self):
        # HJJ: 缓存键基于作者slug和页码
        from uuslug import slugify
        author_name = slugify(self.kwargs['author_name'])
        return f'author_{author_name}_{self.page_number}'

    def get_queryset_data(self):
        # HJJ: 查询指定作者的已发布文章
        author_name = self.kwargs['author_name']
        return self.get_optimized_article_queryset().filter(
            author__username=author_name, type='a', status='p'
        )

    def get_context_data(self, **kwargs):
        author_name = self.kwargs['author_name']
        kwargs['page_type'] = AuthorDetailView.page_type
        kwargs['tag_name'] = author_name
        
        # HJJ: 注入作者页SEO元数据
        blog_setting = get_blog_setting()
        article_count = self.get_queryset().count()
        kwargs['seo_title'] = f"{author_name} 的文章 | {blog_setting.site_name}"
        kwargs['seo_description'] = f"浏览 {author_name} 发表的所有文章，共 {article_count} 篇。"
        kwargs['seo_keywords'] = f"{author_name}, {blog_setting.site_keywords}"
        
        return super(AuthorDetailView, self).get_context_data(**kwargs)


class TagDetailView(SlugCachedMixin, OptimizedArticleQueryMixin, ArticleListView):
    """
    HJJ: 标签列表页面视图（重构版）
    使用 SlugCachedMixin 避免重复查询 Tag
    使用 OptimizedArticleQueryMixin 优化文章查询
    """
    page_type = '分类标签归档'
    slug_url_kwarg = 'tag_name'
    slug_model = Tag

    def get_queryset_data(self):
        # HJJ: 使用Mixin缓存的对象，只查询一次Tag
        tag = self.get_slug_object()
        return self.get_optimized_article_queryset().filter(
            tags__name=tag.name, type='a', status='p'
        )

    def get_queryset_cache_key(self):
        # HJJ: 复用缓存的对象，不再重复查询数据库
        tag = self.get_slug_object()
        return f'tag_{tag.name}_{self.page_number}'

    def get_context_data(self, **kwargs):
        tag = self.get_slug_object()
        kwargs['page_type'] = TagDetailView.page_type
        kwargs['tag_name'] = tag.name
        
        # HJJ: 注入标签页SEO元数据
        blog_setting = get_blog_setting()
        article_count = self.get_queryset().count()
        kwargs['seo_title'] = f"{tag.name} | {blog_setting.site_name}"
        kwargs['seo_description'] = f"浏览所有关于 {tag.name} 的文章，共 {article_count} 篇内容。"
        kwargs['seo_keywords'] = f"{tag.name}, {blog_setting.site_keywords}"
        
        return super(TagDetailView, self).get_context_data(**kwargs)


class ArchivesView(OptimizedArticleQueryMixin, ArticleListView):
    """
    HJJ: 文章归档页面视图（重构版）
    使用 OptimizedArticleQueryMixin 优化文章查询
    不分页，展示所有已发布文章
    """
    page_type = '文章归档'
    paginate_by = None  # HJJ: 不分页
    page_kwarg = None
    template_name = 'blog/article_archives.html'

    def get_queryset_data(self):
        return self.get_optimized_article_queryset().filter(status='p')

    def get_queryset_cache_key(self):
        return 'archives'


class LinkListView(ListView):
    # HJJ: 友情链接列表视图，仅展示已启用的链接
    model = Links
    template_name = 'blog/links_list.html'

    def get_queryset(self):
        return Links.objects.filter(is_enable=True)


class EsSearchView(SearchView):
    # HJJ: Elasticsearch搜索视图，支持搜索结果高亮
    def build_form(self, form_kwargs=None):
        """HJJ: 覆写构建表单方法，启用搜索结果高亮"""
        if form_kwargs is None:
            form_kwargs = {}

        # HJJ: 启用搜索结果高亮
        from haystack.query import SearchQuerySet
        if self.searchqueryset is None:
            sqs = SearchQuerySet().highlight()
        else:
            sqs = self.searchqueryset.highlight()

        form_kwargs['searchqueryset'] = sqs
        return super().build_form(form_kwargs=form_kwargs)

    def get_context(self):
        # HJJ: 构建搜索上下文，包含分页、拼写建议等
        paginator, page = self.build_page()
        context = {
            "query": self.query,
            "form": self.form,
            "page": page,
            "paginator": paginator,
            "suggestion": None,
        }
        if hasattr(self.results, "query") and self.results.query.backend.include_spelling:
            context["suggestion"] = self.results.query.get_spelling_suggestion()
        context.update(self.extra_context())

        return context


@csrf_exempt
def fileupload(request):
    """
    HJJ: 文件上传接口（图床功能）
    需要携带签名认证，支持图片压缩和质量优化
    参数: request - HTTP请求对象，需包含GET参数sign和POST文件数据
    返回: HttpResponse - 成功返回文件URL列表，失败返回403或错误信息
    异常: 无（所有异常由调用方处理）
    """
    if request.method == 'POST':
        # HJJ: 签名验证，防止未授权上传
        sign = request.GET.get('sign', None)
        if not sign:
            return HttpResponseForbidden()
        if not sign == get_sha256(get_sha256(settings.SECRET_KEY)):
            return HttpResponseForbidden()
        response = []
        for filename in request.FILES:
            timestr = timezone.now().strftime('%Y/%m/%d')
            imgextensions = ['jpg', 'png', 'jpeg', 'bmp']
            fname = u''.join(str(filename))
            isimage = len([i for i in imgextensions if fname.find(i) >= 0]) > 0
            # HJJ: 按文件类型分目录存储
            base_dir = os.path.join(settings.STATICFILES, "files" if not isimage else "image", timestr)
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
            # HJJ: 生成唯一文件名，防止冲突
            savepath = os.path.normpath(os.path.join(base_dir, f"{uuid.uuid4().hex}{os.path.splitext(filename)[-1]}"))
            # HJJ: 路径穿越防护
            if not savepath.startswith(base_dir):
                return HttpResponse("only for post")
            # HJJ: 分块写入文件
            with open(savepath, 'wb+') as wfile:
                for chunk in request.FILES[filename].chunks():
                    wfile.write(chunk)
            # HJJ: 图片压缩处理，降低质量至20%
            if isimage:
                from PIL import Image
                image = Image.open(savepath)
                image.save(savepath, quality=20, optimize=True)
            url = static(savepath)
            response.append(url)
        return HttpResponse(response)

    else:
        return HttpResponse("only for post")


# ===== 错误处理视图 =====
# HJJ: 保留旧导入以保持向后兼容
# 实际实现在 djangoblog.error_views 中
# 可在 urls.py 中直接引用新实现

from djangoblog.error_views import (
    page_not_found_view,
    server_error_view,
    permission_denied_view
)


def clean_cache_view(request):
    # HJJ: 手动清理全站缓存的视图接口
    cache.clear()
    return HttpResponse('ok')