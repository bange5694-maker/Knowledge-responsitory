# HJJ: Haystack搜索引擎索引配置模块
# 定义博客文章的搜索索引结构，支持全文检索功能
# 使用模板文件定义索引字段的权重和内容组合

from haystack import indexes

from blog.models import Article


class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    """
    HJJ: 文章搜索索引类
    继承SearchIndex和Indexable，将Article模型映射到Haystack搜索引擎
    
    字段说明:
        text: 主搜索字段，使用模板文件组合多个字段的内容进行全文检索
        title: 单独存储标题字段，用于搜索结果展示
        body: 单独存储正文字段，用于搜索结果展示和高亮
    
    参数:
        document=True: 标记为主文档字段，搜索引擎主要对该字段建立索引
        use_template=True: 使用模板文件定义该字段的内容来源和权重
        model_attr: 直接从模型对应字段取值
        stored=True: 存储原始值，用于搜索结果中直接展示
    """
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', stored=True)
    body = indexes.CharField(model_attr='body', stored=True)

    def get_model(self):
        """
        HJJ: 返回该索引对应的Django模型
        参数: 无
        返回: Model - Article模型类
        """
        return Article

    def index_queryset(self, using=None):
        """
        HJJ: 返回需要建立索引的数据查询集
        仅对已发布的文章建立索引，草稿文章不会被搜索到
        
        参数:
            using: str - 搜索引擎后端标识（如'default'），暂未使用
        返回: QuerySet - 已发布文章的查询集
        """
        return self.get_model().objects.filter(status='p')