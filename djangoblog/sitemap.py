# DH: 这个文件是给搜索引擎看的“地图”，列出网站里有哪些页面，方便百度、谷歌收录。

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Article, Category, Tag


# DH: 几个固定页面的地址，这里只放了首页。
class StaticViewSitemap(Sitemap):
    # DH: 告诉搜索引擎这类页面大概多久变一次、有多重要。
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['blog:index', ]

    def location(self, item):
        return reverse(item)


# DH: 文章的地图，只放已经发布的文章。
class ArticleSiteMap(Sitemap):
    changefreq = "monthly"
    priority = "0.6"

    def items(self):
        return Article.objects.filter(status='p')

    # DH: 最近一次修改时间，搜索引擎按这个判断要不要重新抓。
    def lastmod(self, obj):
        return obj.last_modify_time


# DH: 分类页面的地图。
class CategorySiteMap(Sitemap):
    changefreq = "Weekly"
    priority = "0.6"

    def items(self):
        return Category.objects.all()

    def lastmod(self, obj):
        return obj.last_modify_time


# DH: 标签页面的地图。
class TagSiteMap(Sitemap):
    changefreq = "Weekly"
    priority = "0.3"

    def items(self):
        return Tag.objects.all()

    def lastmod(self, obj):
        return obj.last_modify_time


# DH: 作者页面的地图。
class UserSiteMap(Sitemap):
    changefreq = "Weekly"
    priority = "0.3"

    # DH: 把文章作者去重后列出来，每个作者一个页面。
    def items(self):
        return list(set(map(lambda x: x.author, Article.objects.all())))

    # DH: 作者页的修改时间用注册时间，简单一点。
    def lastmod(self, obj):
        return obj.date_joined
