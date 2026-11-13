# XJN: 模块功能：评论邮件通知工具，负责在评论/回复提交后向评论者或父评论作者发送提醒邮件。
import logging

from django.utils.translation import gettext_lazy as _

from djangoblog.utils import get_current_site
from djangoblog.utils import send_email

logger = logging.getLogger(__name__)


# XJN: 功能：发送评论通知邮件；先向本条评论作者发送感谢邮件，若为回复再向父评论作者发送回复提醒。
# XJN: 入参 comment：已保存的 Comment 实例（需含 author、article 及可选的 parent_comment）。
# XJN: 返回值：无。
# XJN: 异常：发送回复提醒时捕获所有异常并写入 logger，避免影响评论提交流程。
def send_comment_email(comment):
    # XJN: 读取当前站点域名，拼接文章绝对地址用于邮件正文中的链接。
    site = get_current_site().domain
    subject = _('Thanks for your comment')
    article_url = f"https://{site}{comment.article.get_absolute_url()}"
    # XJN: 构造面向评论作者的中文/系统语言感谢邮件正文。
    html_content = _("""<p>Thank you very much for your comments on this site</p>
                    You can visit <a href="%(article_url)s" rel="bookmark">%(article_title)s</a>
                    to review your comments,
                    Thank you again!
                    <br />
                    If the link above cannot be opened, please copy this link to your browser.
                    %(article_url)s""") % {'article_url': article_url, 'article_title': comment.article.title}
    tomail = comment.author.email
    # XJN: 向评论作者本人发送感谢邮件。
    send_email([tomail], subject, html_content)
    try:
        # XJN: 仅当本条评论是回复（存在父评论）时，额外通知父评论作者。
        if comment.parent_comment:
            html_content = _("""Your comment on <a href="%(article_url)s" rel="bookmark">%(article_title)s</a><br/> has 
                   received a reply. <br/> %(comment_body)s
                    <br/>   
                    go check it out!
                     <br/>
                     If the link above cannot be opened, please copy this link to your browser.
                     %(article_url)s
                    """) % {'article_url': article_url, 'article_title': comment.article.title,
                            'comment_body': comment.parent_comment.body}
            tomail = comment.parent_comment.author.email
            # XJN: 向被回复的父评论作者发送回复提醒邮件。
            send_email([tomail], subject, html_content)
    except Exception as e:
        # XJN: 邮件发送失败只记录错误，不向调用方抛出，保证评论提交成功。
        logger.error(e)
