# DH: 这个文件是“信号”处理：数据库里一保存东西、用户一登录，就自动做点事，比如清缓存、通知百度、发邮件。

import _thread
import logging

import django.dispatch
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver

from comments.models import Comment
from comments.utils import send_comment_email
from djangoblog.spider_notify import SpiderNotify
from djangoblog.utils import cache, expire_view_cache, delete_sidebar_cache, delete_view_cache
from djangoblog.utils import get_current_site
from oauth.models import OAuthUser

logger = logging.getLogger(__name__)

# DH: 自定义两个信号：一个用来发邮件，一个用来处理第三方登录后的头像和缓存。
oauth_user_login_signal = django.dispatch.Signal(['id'])
send_email_signal = django.dispatch.Signal(
    ['emailto', 'title', 'content'])


# DH: 真正发邮件的地方：组一封 HTML 邮件发出去，再把发送结果写进日志表。
@receiver(send_email_signal)
def send_email_signal_handler(sender, **kwargs):
    emailto = kwargs['emailto']
    title = kwargs['title']
    content = kwargs['content']

    # DH: 用 Django 的邮件类，正文按 HTML 处理。
    msg = EmailMultiAlternatives(
        title,
        content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=emailto)
    msg.content_subtype = "html"

    # DH: 先建一条日志记录，发成功还是失败都写进去。
    from servermanager.models import EmailSendLog
    log = EmailSendLog()
    log.title = title
    log.content = content
    log.emailto = ','.join(emailto)

    try:
        result = msg.send()
        log.send_result = result > 0
    except Exception as e:
        # DH: 发失败也不能让调用方崩，记下错误就好。
        logger.error(f"失败邮箱号: {emailto}, {e}")
        log.send_result = False
    log.save()


# DH: 第三方登录后，如果头像还是外站的，就下载保存到本站，再把侧边栏缓存清掉。
@receiver(oauth_user_login_signal)
def oauth_user_login_signal_handler(sender, **kwargs):
    id = kwargs['id']
    oauthuser = OAuthUser.objects.get(id=id)
    site = get_current_site().domain
    if oauthuser.picture and not oauthuser.picture.find(site) >= 0:
        from djangoblog.utils import save_user_avatar
        oauthuser.picture = save_user_avatar(oauthuser.picture)
        oauthuser.save()

    delete_sidebar_cache()


# DH: 任何模型保存后都会走到这里，按情况清理缓存、通知百度。
@receiver(post_save)
def model_post_save_callback(
        sender,
        instance,
        created,
        raw,
        using,
        update_fields,
        **kwargs):
    # DH: 后台操作日志自己的保存不用管，跳过。
    if isinstance(instance, LogEntry):
        return

    # 检查是否只更新了浏览量
    # DH: 如果只是浏览量加 1，不用清缓存，省点事。
    is_update_views = update_fields == {'views'}
    if is_update_views:
        return  # 浏览量更新不需要清理缓存

    # 搜索引擎通知
    # DH: 模型如果有 get_full_url，就把地址推给百度；测试环境不推。
    if 'get_full_url' in dir(instance):
        if not settings.TESTING:
            try:
                notify_url = instance.get_full_url()
                SpiderNotify.baidu_notify([notify_url])
            except Exception as ex:
                logger.error("notify sipder", ex)

    # 评论相关的缓存清理
    # DH: 评论保存后：清文章页、评论、侧边栏、SEO 的缓存，再开个线程发通知邮件。
    if isinstance(instance, Comment):
        if instance.is_enable:
            path = instance.article.get_absolute_url()
            site = get_current_site().domain
            if site.find(':') > 0:
                site = site[0:site.find(':')]

            expire_view_cache(
                path,
                servername=site,
                serverport=80,
                key_prefix='blogdetail')

            # 清理评论相关缓存
            comment_cache_key = 'article_comments_{id}'.format(
                id=instance.article.id)
            cache.delete(comment_cache_key)
            delete_view_cache('article_comments', [str(instance.article.pk)])
            delete_sidebar_cache()
            cache.delete('seo_processor')

            # DH: 邮件通知单独开线程发，不卡住保存评论的请求。
            _thread.start_new_thread(send_comment_email, (instance,))

    # 文章相关的精细化缓存清理
    # DH: 文章变化后，把首页、详情、分类、标签、作者、归档的缓存都清掉，不然页面还是旧的。
    elif 'get_full_url' in dir(instance):
        from blog.models import Article, Category, Tag

        if isinstance(instance, Article):
            # 清理文章列表首页缓存
            cache.delete('index_1')

            # 清理文章详情缓存
            article_cache_key = f'article_comments_{instance.id}'
            cache.delete(article_cache_key)

            # 清理分类相关缓存
            if instance.category:
                category_name = instance.category.name
                cache.delete(f'category_list_{category_name}_1')

            # 清理标签相关缓存
            try:
                for tag in instance.tags.all():
                    cache.delete(f'tag_{tag.name}_1')
            except Exception:
                # DH: 刚创建文章时标签可能还没关联好，这里容错一下。
                pass  # 可能在创建时tags还未关联

            # 清理作者相关缓存
            if instance.author:
                from uuslug import slugify
                author_slug = slugify(instance.author.username)
                cache.delete(f'author_{author_slug}_1')

            # 清理归档缓存
            cache.delete('archives')

            # 清理侧边栏和上下文处理器缓存
            delete_sidebar_cache()
            cache.delete('seo_processor')

        elif isinstance(instance, Category):
            # 清理分类相关缓存
            cache.delete(f'category_list_{instance.name}_1')
            delete_sidebar_cache()
            cache.delete('seo_processor')

        elif isinstance(instance, Tag):
            # 清理标签相关缓存
            cache.delete(f'tag_{instance.name}_1')
            delete_sidebar_cache()

        # 其他模型的缓存清理
        else:
            # 对于其他有get_full_url的模型，清理基础缓存
            delete_sidebar_cache()
            cache.delete('seo_processor')


# DH: 用户登录或退出后，清一下侧边栏缓存。
@receiver(user_logged_in)
@receiver(user_logged_out)
def user_auth_callback(sender, request, user, **kwargs):
    if user and user.username:
        logger.info(user)
        delete_sidebar_cache()
        # cache.clear()
