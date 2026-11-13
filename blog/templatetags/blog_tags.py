# HJJ: 博客模板标签与过滤器模块
# 提供Markdown渲染、SEO数据、侧边栏、分页、头像、搜索高亮、插件系统等自定义模板功能

import hashlib
import json
import logging
import random
import urllib

from django import template
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import stringfilter
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe

from blog.models import Article, Category, Tag, Links, SideBar, LinkShowType
from comments.models import Comment
from djangoblog.utils import CommonMarkdown, sanitize_html
from djangoblog.utils import cache
from djangoblog.utils import get_current_site
from oauth.models import OAuthUser
from djangoblog.plugin_manage import hooks

logger = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag(takes_context=True)
def head_meta(context):
    # HJJ: 插件钩子 - 允许插件向<head>标签注入自定义meta元素
    return mark_safe(hooks.apply_filters('head_meta', '', context))


@register.simple_tag
def timeformat(data):
    # HJJ: 格式化时间为时分秒格式
    try:
        return data.strftime(settings.TIME_FORMAT)
    except Exception as e:
        logger.error(e)
        return ""


@register.simple_tag
def datetimeformat(data):
    # HJJ: 格式化时间为年月日时分秒格式
    try:
        return data.strftime(settings.DATE_TIME_FORMAT)
    except Exception as e:
        logger.error(e)
        return ""


@register.filter()
@stringfilter
def custom_markdown(content):
    """
    HJJ: 通用Markdown过滤器，应用于文章内容处理
    先转换为HTML，再应用插件过滤器优化输出
    
    参数:
        content: str - Markdown格式的原始内容
    返回:
        SafeString - 安全的HTML字符串
    """
    html_content = CommonMarkdown.get_markdown(content)
    
    # HJJ: 应用插件过滤器优化HTML（如代码高亮、懒加载等）
    from djangoblog.plugin_manage import hooks
    from djangoblog.plugin_manage.hook_constants import ARTICLE_CONTENT_HOOK_NAME
    optimized_html = hooks.apply_filters(ARTICLE_CONTENT_HOOK_NAME, html_content)
    
    return mark_safe(optimized_html)


@register.filter()
@stringfilter
def sidebar_markdown(content):
    # HJJ: 侧边栏Markdown渲染（不含插件过滤）
    html_content = CommonMarkdown.get_markdown(content)
    return mark_safe(html_content)


@register.simple_tag(takes_context=True)
def render_article_content(context, article, is_summary=False):
    """
    HJJ: 渲染文章内容，包含完整上下文供插件使用
    
    参数:
        context: dict - 模板上下文
        article: Article - 文章对象
        is_summary: bool - 是否为摘要模式（首页列表使用）
    返回:
        SafeString - 渲染后的HTML内容
    """
    if not article or not hasattr(article, 'body'):
        return ''
    
    # HJJ: 先转换Markdown为HTML
    html_content = CommonMarkdown.get_markdown(article.body)
    
    # HJJ: 摘要模式：截断内容后再应用插件
    if is_summary:
        from djangoblog.utils import get_blog_setting
        from django.template.defaultfilters import truncatechars_html

        blogsetting = get_blog_setting()
        summary_length = blogsetting.article_sub_length

        # HJJ: 使用truncatechars_html保留HTML标签结构
        html_content = truncatechars_html(html_content, summary_length)
    
    # HJJ: 应用插件过滤器，传递完整上下文
    from djangoblog.plugin_manage import hooks
    from djangoblog.plugin_manage.hook_constants import ARTICLE_CONTENT_HOOK_NAME
    
    request = context.get('request')
    
    optimized_html = hooks.apply_filters(
        ARTICLE_CONTENT_HOOK_NAME,
        html_content,
        article=article,
        request=request,
        context=context,
        is_summary=is_summary  # HJJ: 传递摘要标志，插件可据此调整行为
    )

    # HJJ: 搜索高亮处理
    query = context.get('query')
    if query and is_summary:
        optimized_html = highlight_content(optimized_html, query)

    return mark_safe(optimized_html)


@register.simple_tag
def get_markdown_toc(content):
    # HJJ: 获取Markdown内容的目录（Table of Contents）
    from djangoblog.utils import CommonMarkdown
    body, toc = CommonMarkdown.get_markdown_with_toc(content)
    return mark_safe(toc)


@register.simple_tag
def current_nav_item(request):
    # HJJ: 根据当前URL路径确定高亮的导航项
    path = request.path
    if path == '/' or path.startswith('/page/'):
        return 'index'
    elif path.startswith('/archives'):
        return 'archives'
    elif path.startswith('/links'):
        return 'links'
    elif path.startswith('/category/'):
        return 'category'
    elif path.startswith('/tag/'):
        return 'category'
    return ''


@register.filter()
@stringfilter
def comment_markdown(content):
    # HJJ: 评论Markdown渲染，附带XSS过滤
    content = CommonMarkdown.get_markdown(content)
    return mark_safe(sanitize_html(content))


@register.filter(is_safe=True)
def to_json(value):
    """
    HJJ: 将Python对象转换为JSON字符串，用于模板中传递给JavaScript
    支持emoji等Unicode字符
    """
    try:
        return mark_safe(json.dumps(value, ensure_ascii=False))
    except (TypeError, ValueError):
        return mark_safe('{}')


@register.filter
def get_reactions_for_user(comment, user):
    # HJJ: 获取评论的表情反应数据（过滤器方式）
    try:
        return comment.get_reactions_summary(user if user.is_authenticated else None)
    except Exception as e:
        logger.error(f"Error getting reactions for comment {comment.id}: {e}")
        return {}


@register.filter(is_safe=True)
@stringfilter
def truncatechars_content(content):
    # HJJ: 截断HTML内容到指定长度（从站点配置读取）
    from django.template.defaultfilters import truncatechars_html
    from djangoblog.utils import get_blog_setting
    blogsetting = get_blog_setting()
    return truncatechars_html(content, blogsetting.article_sub_length)


@register.filter(is_safe=True)
@stringfilter
def truncate(content):
    # HJJ: 去除HTML标签后截取前150个字符
    from django.utils.html import strip_tags
    return strip_tags(content)[:150]


@register.inclusion_tag('blog/tags/breadcrumb.html')
def load_breadcrumb(article):
    """
    HJJ: 生成文章面包屑导航
    参数:
        article: Article - 文章对象
    返回:
        dict - 包含面包屑层级信息的上下文
    """
    names = article.get_category_tree()
    from djangoblog.utils import get_blog_setting
    blogsetting = get_blog_setting()
    site = get_current_site().domain
    names.append((blogsetting.site_name, '/'))
    names = names[::-1]  # HJJ: 反转顺序，从根到叶

    return {
        'names': names,
        'title': article.title,
        'count': len(names) + 1
    }


@register.inclusion_tag('blog/tags/article_tag_list.html')
def load_articletags(article):
    """
    HJJ: 加载文章标签列表（含随机颜色）
    参数:
        article: Article - 文章对象
    返回:
        dict - 标签列表上下文
    """
    tags = article.tags.all()
    tags_list = []
    for tag in tags:
        url = tag.get_absolute_url()
        count = tag.get_article_count()
        tags_list.append((
            url, count, tag, random.choice(settings.BOOTSTRAP_COLOR_TYPES)
        ))
    return {
        'article_tags_list': tags_list
    }


@register.inclusion_tag('blog/tags/sidebar.html')
def load_sidebar(user, linktype):
    """
    HJJ: 加载侧边栏内容（带3天缓存）
    
    参数:
        user: User - 当前登录用户
        linktype: str - 友情链接展示类型
    返回:
        dict - 侧边栏所有组件的上下文
    """
    value = cache.get("sidebar" + linktype)
    if value:
        value['user'] = user
        return value
    else:
        logger.info('load sidebar')
        from djangoblog.utils import get_blog_setting
        blogsetting = get_blog_setting()

        # HJJ: 优化查询：使用select_related/prefetch_related减少N+1查询
        recent_articles = Article.objects.filter(
            status='p'
        ).select_related('author', 'category')[:blogsetting.sidebar_article_count]

        sidebar_categorys = Category.objects.all()

        extra_sidebars = SideBar.objects.filter(
            is_enable=True
        ).order_by('sequence')

        most_read_articles = Article.objects.filter(
            status='p'
        ).select_related('author', 'category').order_by(
            '-views'
        )[:blogsetting.sidebar_article_count]

        dates = Article.objects.datetimes('creation_time', 'month', order='DESC')

        links = Links.objects.filter(is_enable=True).filter(
            Q(show_type=str(linktype)) | Q(show_type=LinkShowType.A)
        )

        commment_list = Comment.objects.filter(
            is_enable=True
        ).select_related('author').order_by('-id')[:blogsetting.sidebar_comment_count]
        
        # HJJ: 标签云计算 - 按文章数排序取Top20，字体大小=(count/avg)*5+10
        increment = 5
        tags = Tag.objects.all()
        sidebar_tags = None
        if tags and len(tags) > 0:
            s = sorted(
                [t for t in [(t, t.get_article_count()) for t in tags] if t[1]],
                key=lambda x: x[1], reverse=True
            )[:20]
            count = sum([t[1] for t in s])
            dd = 1 if (count == 0 or not len(s)) else count / len(s)
            sidebar_tags = list(
                map(lambda x: (x[0], x[1], (x[1] / dd) * increment + 10), s))

        value = {
            'recent_articles': recent_articles,
            'sidebar_categorys': sidebar_categorys,
            'most_read_articles': most_read_articles,
            'article_dates': dates,
            'sidebar_comments': commment_list,
            'sidabar_links': links,
            'show_google_adsense': blogsetting.show_google_adsense,
            'google_adsense_codes': blogsetting.google_adsense_codes,
            'open_site_comment': blogsetting.open_site_comment,
            'show_gongan_code': blogsetting.show_gongan_code,
            'sidebar_tags': sidebar_tags,
            'extra_sidebars': extra_sidebars
        }
        # HJJ: 设置3天缓存
        cache.set("sidebar" + linktype, value, 60 * 60 * 60 * 3)
        logger.info('set sidebar cache.key:{key}'.format(key="sidebar" + linktype))
        value['user'] = user
        return value


@register.inclusion_tag('blog/tags/article_meta_info.html')
def load_article_metas(article, user):
    # HJJ: 加载文章元信息（作者、发布时间等）
    return {
        'article': article,
        'user': user
    }


@register.inclusion_tag('blog/tags/article_pagination.html')
def load_pagination_info(page_obj, page_type, tag_name):
    """
    HJJ: 生成分页导航HTML（含智能页码范围）
    
    参数:
        page_obj: Page - Django分页对象
        page_type: str - 页面类型（首页/分类/标签/作者）
        tag_name: str - 分类/标签/作者名称
    返回:
        dict - 包含上/下页URL和页码范围
    """
    previous_url = ''
    next_url = ''

    # HJJ: 预解析slug，避免重复数据库查询
    _slug = None
    if page_type == '分类标签归档':
        _slug = get_object_or_404(Tag, name=tag_name).slug
    elif page_type == '分类目录归档':
        _slug = get_object_or_404(Category, name=tag_name).slug

    def _build_url(page_number):
        # HJJ: 根据页面类型构建分页URL
        if page_type == '':
            return reverse('blog:index_page', kwargs={'page': page_number})
        elif page_type == '分类标签归档':
            return reverse('blog:tag_detail_page',
                           kwargs={'page': page_number, 'tag_name': _slug})
        elif page_type == '作者文章归档':
            return reverse('blog:author_detail_page',
                           kwargs={'page': page_number, 'author_name': tag_name})
        elif page_type == '分类目录归档':
            return reverse('blog:category_detail_page',
                           kwargs={'page': page_number, 'category_name': _slug})
        return ''

    if page_obj.has_next():
        next_url = _build_url(page_obj.next_page_number())
    if page_obj.has_previous():
        previous_url = _build_url(page_obj.previous_page_number())

    # HJJ: 构建智能页码范围（最多显示7个页码，含省略号）
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages
    page_range = []

    if total_pages > 1:
        if total_pages <= 7:
            nums = range(1, total_pages + 1)
        else:
            nums = set()
            nums.add(1)
            nums.add(total_pages)
            for i in range(max(1, current_page - 2), min(total_pages + 1, current_page + 3)):
                nums.add(i)
            nums = sorted(nums)

        last_num = 0
        for num in nums:
            if num - last_num > 1:
                page_range.append({'type': 'ellipsis'})
            page_range.append({
                'type': 'page',
                'number': num,
                'url': _build_url(num),
                'is_current': num == current_page,
            })
            last_num = num

    return {
        'previous_url': previous_url,
        'next_url': next_url,
        'page_obj': page_obj,
        'page_range': page_range,
    }


@register.inclusion_tag('blog/tags/article_info.html')
def load_article_detail(article, isindex, user, query=None):
    """
    HJJ: 加载文章详情（列表页或详情页共用）
    
    参数:
        article: Article - 文章对象
        isindex: bool - 是否列表页（列表页只显示摘要）
        user: User - 当前用户
        query: str - 搜索查询词（用于高亮）
    返回:
        dict - 文章详情上下文
    """
    from djangoblog.utils import get_blog_setting
    blogsetting = get_blog_setting()

    return {
        'article': article,
        'isindex': isindex,
        'user': user,
        'query': query,
        'open_site_comment': blogsetting.open_site_comment,
    }


@register.inclusion_tag('blog/tags/article_info_highlight.html')
def load_article_detail_with_highlight(article, highlighted, isindex, user):
    # HJJ: 加载带搜索高亮的文章详情
    from djangoblog.utils import get_blog_setting
    blogsetting = get_blog_setting()

    return {
        'article': article,
        'highlighted': highlighted,
        'isindex': isindex,
        'user': user,
        'open_site_comment': blogsetting.open_site_comment,
    }


@register.filter
def highlight_search_term(text, query):
    """
    HJJ: 在纯文本中高亮搜索关键词（使用<mark>标签）
    
    参数:
        text: str - 原始文本
        query: str - 搜索查询词（支持空格分隔的多词）
    返回:
        SafeString - 高亮后的HTML
    """
    if not query or not text:
        return text

    import re
    terms = query.split()

    for term in terms:
        if len(term) < 2:  # HJJ: 忽略单字符词
            continue
        pattern = re.compile(r'(' + re.escape(term) + r')', re.IGNORECASE)
        text = pattern.sub(r'<mark>\1</mark>', text)

    return mark_safe(text)


@register.filter
def highlight_content(html_content, query):
    """
    HJJ: 对HTML内容提取纯文本后进行搜索高亮
    跳过代码块中的内容，避免破坏代码结构
    
    参数:
        html_content: str - HTML内容
        query: str - 搜索查询词
    返回:
        SafeString - 高亮后的纯文本（含mark标签）
    """
    if not query or not html_content:
        return html_content

    from bs4 import BeautifulSoup
    import re

    soup = BeautifulSoup(html_content, 'html.parser')

    # HJJ: 移除代码块、脚本等标签（不索引其内容）
    for tag in soup.find_all(['code', 'pre', 'script', 'style']):
        tag.decompose()

    text = soup.get_text(separator=' ', strip=True)

    terms = [term for term in query.split() if len(term) >= 2]

    if not terms:
        return text

    for term in terms:
        pattern = re.compile(r'(' + re.escape(term) + r')', re.IGNORECASE)
        text = pattern.sub(r'<mark>\1</mark>', text)

    return mark_safe(text)


@register.filter
def gravatar_url(email, size=40):
    """
    HJJ: 获取用户头像URL
    优先使用OAuth第三方头像，否则返回默认头像
    
    参数:
        email: str - 用户邮箱
        size: int - 头像尺寸（像素）
    返回:
        str - 头像URL
    """
    cachekey = 'avatar/' + email
    url = cache.get(cachekey)
    if url:
        return url
    
    # HJJ: 检查OAuth用户是否有自定义头像
    usermodels = OAuthUser.objects.filter(email=email)
    if usermodels:
        users_with_picture = list(filter(lambda x: x.picture is not None, usermodels))
        if users_with_picture:
            default_avatar_path = static('blog/img/avatar.png')
            
            # HJJ: 优先选择非默认头像
            non_default_users = [u for u in users_with_picture if u.picture != default_avatar_path and not u.picture.endswith('/avatar.png')]
            selected_user = non_default_users[0] if non_default_users else users_with_picture[0]
            
            url = selected_user.picture
            cache.set(cachekey, url, 60 * 60 * 24)  # HJJ: 缓存24小时
            
            avatar_type = 'non-default' if non_default_users else 'default'
            logger.info('Using {} OAuth avatar for {} from {}'.format(avatar_type, email, selected_user.type))
            return url
    
    # HJJ: 使用默认头像
    url = static('blog/img/avatar.png')
    cache.set(cachekey, url, 60 * 60 * 24)
    logger.info('Using default avatar for {}'.format(email))
    return url


@register.filter
def gravatar(email, size=40):
    # HJJ: 获取用户头像HTML img标签
    url = gravatar_url(email, size)
    return mark_safe(
        '<img src="%s" height="%d" width="%d" class="avatar" alt="用户头像">' %
        (url, size, size))


@register.simple_tag
def query(qs, **kwargs):
    # HJJ: 模板标签 - 对查询集进行过滤
    return qs.filter(**kwargs)


@register.filter
def addstr(arg1, arg2):
    # HJJ: 字符串拼接过滤器
    return str(arg1) + str(arg2)


# === 插件系统模板标签 ===

@register.simple_tag(takes_context=True)
def render_plugin_widgets(context, position, **kwargs):
    """
    HJJ: 渲染指定位置的所有插件组件
    
    参数:
        context: dict - 模板上下文
        position: str - 位置标识（如'sidebar', 'footer'）
        **kwargs: 传递给插件的额外参数
    返回:
        SafeString - 所有插件HTML拼接结果
    """
    from djangoblog.plugin_manage.loader import get_loaded_plugins
    
    widgets = []
    
    for plugin in get_loaded_plugins():
        try:
            widget_data = plugin.render_position_widget(
                position=position,
                context=context,
                **kwargs
            )
            if widget_data:
                widgets.append(widget_data)
        except Exception as e:
            logger.error(f"Error rendering widget from plugin {plugin.PLUGIN_NAME}: {e}")
    
    # HJJ: 按优先级排序（数字越小优先级越高）
    widgets.sort(key=lambda x: x['priority'])
    
    html_parts = [widget['html'] for widget in widgets]
    return mark_safe(''.join(html_parts))


@register.simple_tag(takes_context=True)
def plugin_critical_head_resources(context):
    # HJJ: 渲染所有插件的关键head资源（阻塞式加载，用于防闪烁脚本）
    from djangoblog.plugin_manage.loader import get_loaded_plugins

    resources = []

    for plugin in get_loaded_plugins():
        try:
            critical_html = plugin.get_critical_head_html(context)
            if critical_html:
                resources.append(critical_html)
        except Exception as e:
            logger.error(f"Error loading critical head resources from plugin {plugin.PLUGIN_NAME}: {e}")

    return mark_safe('\n'.join(resources))


@register.simple_tag(takes_context=True)
def plugin_head_resources(context):
    # HJJ: 渲染所有插件的head资源（仅自定义HTML，CSS已集成到压缩系统）
    from djangoblog.plugin_manage.loader import get_loaded_plugins

    resources = []

    for plugin in get_loaded_plugins():
        try:
            head_html = plugin.get_head_html(context)
            if head_html:
                resources.append(head_html)
        except Exception as e:
            logger.error(f"Error loading head resources from plugin {plugin.PLUGIN_NAME}: {e}")

    return mark_safe('\n'.join(resources))


@register.simple_tag(takes_context=True)
def plugin_body_resources(context):
    # HJJ: 渲染所有插件的body资源（仅自定义HTML，JS已集成到压缩系统）
    from djangoblog.plugin_manage.loader import get_loaded_plugins
    
    resources = []
    
    for plugin in get_loaded_plugins():
        try:
            body_html = plugin.get_body_html(context)
            if body_html:
                resources.append(body_html)
        except Exception as e:
            logger.error(f"Error loading body resources from plugin {plugin.PLUGIN_NAME}: {e}")
    
    return mark_safe('\n'.join(resources))


@register.inclusion_tag('plugins/css_includes.html')
def plugin_compressed_css():
    # HJJ: 渲染所有插件的CSS文件列表（用于压缩合并）
    from djangoblog.plugin_manage.loader import get_loaded_plugins
    
    css_files = []
    for plugin in get_loaded_plugins():
        for css_file in plugin.get_css_files():
            css_url = plugin.get_static_url(css_file)
            css_files.append(css_url)
    
    return {'css_files': css_files}


@register.inclusion_tag('plugins/js_includes.html')
def plugin_compressed_js():
    # HJJ: 渲染所有插件的JS文件列表（用于压缩合并）
    from djangoblog.plugin_manage.loader import get_loaded_plugins
    
    js_files = []
    for plugin in get_loaded_plugins():
        for js_file in plugin.get_js_files():
            js_url = plugin.get_static_url(js_file)
            js_files.append(js_url)
    
    return {'js_files': js_files}


@register.simple_tag(takes_context=True)
def plugin_widget(context, plugin_name, widget_type='default', **kwargs):
    # HJJ: 渲染指定插件的特定组件
    from djangoblog.plugin_manage.loader import get_plugin_by_slug
    
    plugin = get_plugin_by_slug(plugin_name)
    if plugin and hasattr(plugin, 'render_template'):
        try:
            widget_context = {**context.flatten(), **kwargs}
            template_name = f"{widget_type}.html"
            return mark_safe(plugin.render_template(template_name, widget_context))
        except Exception as e:
            logger.error(f"Error rendering plugin widget {plugin_name}.{widget_type}: {e}")
    
    return ""