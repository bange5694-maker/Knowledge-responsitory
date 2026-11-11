# DH: 这个文件做 RSS 订阅，别人用阅读器订阅后，这里把最新文章打包给他。

from django.contrib.auth import get_user_model
from django.contrib.syndication.views import Feed
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed

from blog.models import Article
from djangoblog.utils import CommonMarkdown


# DH: RSS 源，格式用标准的 RSS 2.0 就行。
class DjangoBlogFeed(Feed):
    # DH: 指定 RSS 的版本。
    feed_type = Rss201rev2Feed

    # DH: 订阅里显示的站点介绍、名字和地址。
    description = '大巧无工,重剑无锋.'
    title = "且听风吟 大巧无工,重剑无锋. "
    link = "/feed/"

    # DH: 作者名取数据库里的第一个用户，也就是站长。
    def author_name(self):
        return get_user_model().objects.first().nickname

    # DH: 作者的链接，还是取第一个用户的主页。
    def author_link(self):
        return get_user_model().objects.first().get_absolute_url()

    # DH: 只挑已发布（status='p'）的文章，按时间倒序取最新 5 篇。
    def items(self):
        return Article.objects.filter(type='a', status='p').order_by('-pub_time')[:5]

    # DH: 每篇文章的标题。
    def item_title(self, item):
        return item.title

    # DH: 正文先转成 Markdown 再放进去，不然阅读器里排版会乱。
    def item_description(self, item):
        return CommonMarkdown.get_markdown(item.body)

    # DH: 版权信息，年份用当前年份。
    def feed_copyright(self):
        now = timezone.now()
        return "Copyright© {year} 且听风吟".format(year=now.year)

    # DH: 文章的正式地址。
    def item_link(self, item):
        return item.get_absolute_url()

    # DH: 不单独给编号，让阅读器用文章链接来区分。
    def item_guid(self, item):
        return
