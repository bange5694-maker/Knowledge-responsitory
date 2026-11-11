# LZH: 模块功能：封装微信机器人所需的博客数据查询接口——关键词检索文章、分类目录、
# LZH: 分类下文章与最新文章，统一限制单次返回条数，避免图文消息过长。

from haystack.query import SearchQuerySet

from blog.models import Article, Category


# LZH: 博客数据接口类：对 haystack 全文检索与 Django ORM 查询做统一封装，供微信机器人调用。
class BlogApi:
    # LZH: 方法说明：初始化检索对象与单次返回条数上限。
    # LZH: 参数：无；返回：None；异常：haystack 检索后端不可用时，SearchQuerySet 构造可能抛异常。
    def __init__(self):
        self.searchqueryset = SearchQuerySet()
        # LZH: 先做一次空查询，让检索对象完成与后端索引的绑定。
        self.searchqueryset.auto_query('')
        # LZH: 单次最多返回 8 条，控制微信图文卡片的数量。
        self.__max_takecount__ = 8

    # LZH: 方法说明：按关键词检索文章，返回命中结果及其数据库对象，最多 8 条。
    # LZH: 参数：query — 用户输入的关键词字符串；返回：SearchQuerySet 切片结果；
    # LZH: 异常：检索索引不可用时由 haystack 抛出，交由上层处理。
    def search_articles(self, query):
        sqs = self.searchqueryset.auto_query(query)
        # LZH: load_all() 一次性取出检索结果对应的数据库对象，避免逐条回表查询。
        sqs = sqs.load_all()
        return sqs[:self.__max_takecount__]

    # LZH: 方法说明：查询全部文章分类，用于 category 命令。
    # LZH: 参数：无；返回：QuerySet[Category]；异常：数据库异常向上抛出。
    def get_category_lists(self):
        return Category.objects.all()

    # LZH: 方法说明：按分类名查询该分类下的文章，最多 8 条。
    # LZH: 参数：categoryname — 分类名称；返回：QuerySet[Article]，无文章时返回 None；
    # LZH: 异常：数据库异常向上抛出。
    def get_category_articles(self, categoryname):
        articles = Article.objects.filter(category__name=categoryname)
        if articles:
            return articles[:self.__max_takecount__]
        return None

    # LZH: 方法说明：查询最新文章列表，最多 8 条，用于 recent 命令。
    # LZH: 参数：无；返回：QuerySet[Article]；异常：数据库异常向上抛出。
    def get_recent_articles(self):
        return Article.objects.all()[:self.__max_takecount__]
