# DH: 这个文件是搜索引擎的 Elasticsearch 版本，负责把文章写进索引、按关键词查出来。

from django.utils.encoding import force_str
from elasticsearch_dsl import Q
from haystack.backends import BaseEngine, BaseSearchBackend, BaseSearchQuery, log_query
from haystack.forms import ModelSearchForm
from haystack.models import SearchResult
from haystack.utils import log as logging

from blog.documents import ArticleDocument, ArticleDocumentManager
from blog.models import Article

logger = logging.getLogger(__name__)


# DH: ES 的后端实现，建索引、更新、删除、搜索都在这里。
class ElasticSearchBackend(BaseSearchBackend):
    # DH: 初始化时建一个文档管理对象，后面增删改索引都靠它。
    def __init__(self, connection_alias, **connection_options):
        super(
            ElasticSearchBackend,
            self).__init__(
            connection_alias,
            **connection_options)
        self.manager = ArticleDocumentManager()
        self.include_spelling = True

    # DH: 把传进来的文章对象转成 ES 里的文档；没传就取全部文章。
    def _get_models(self, iterable):
        models = iterable if iterable and iterable[0] else Article.objects.all()
        docs = self.manager.convert_to_doc(models)
        return docs

    # DH: 建索引并把文章导进去。
    def _create(self, models):
        self.manager.create_index()
        docs = self._get_models(models)
        self.manager.rebuild(docs)

    # DH: 从索引里删掉这些文档。
    def _delete(self, models):
        for m in models:
            m.delete()
        return True

    # DH: 重建索引里的文档。
    def _rebuild(self, models):
        models = models if models else Article.objects.all()
        docs = self.manager.convert_to_doc(models)
        self.manager.update_docs(docs)

    # DH: 文章有变化时更新对应的索引。
    def update(self, index, iterable, commit=True):

        models = self._get_models(iterable)
        self.manager.update_docs(models)

    # DH: 文章删除时把索引里的也删掉。
    def remove(self, obj_or_string):
        models = self._get_models([obj_or_string])
        self._delete(models)

    # DH: 清空索引。
    def clear(self, models=None, commit=True):
        self.remove(None)

    # DH: 查不到时给个推荐词：用 ES 的 suggest 找相近的词，找不到就用原词。
    @staticmethod
    def get_suggestion(query: str) -> str:
        """获取推荐词, 如果没有找到添加原搜索词"""

        search = ArticleDocument.search() \
            .query("match", body=query) \
            .suggest('suggest_search', query, term={'field': 'body'}) \
            .execute()

        keywords = []
        for suggest in search.suggest.suggest_search:
            if suggest["options"]:
                keywords.append(suggest["options"][0]["text"])
            else:
                keywords.append(suggest["text"])

        return ' '.join(keywords)

    # DH: 真正搜索的地方：先按标题和正文匹配，只要已发布文章；需要高亮就把命中的词包上 <mark>。
    @log_query
    def search(self, query_string, **kwargs):
        logger.info('search query_string:' + query_string)

        # DH: 分页用的起止位置。
        start_offset = kwargs.get('start_offset')
        end_offset = kwargs.get('end_offset')
        # DH: 默认要高亮。
        highlight = kwargs.get('highlight', True)  # 默认启用高亮

        # 推荐词搜索
        # DH: 如果开了推荐词，就先找相近的词来搜。
        if getattr(self, "is_suggest", None):
            suggestion = self.get_suggestion(query_string)
        else:
            suggestion = query_string

        # DH: 标题或正文命中一个就算匹配。
        q = Q('bool',
              should=[Q('match', body=suggestion), Q('match', title=suggestion)],
              minimum_should_match=1)  # 至少匹配1个should子句

        # DH: 只搜已发布的文章（status='p'，type='a'）。
        search = ArticleDocument.search() \
                     .query('bool', filter=[q]) \
                     .filter('term', status='p') \
                     .filter('term', type='a')

        # 添加高亮配置
        # DH: 高亮设置：每段取 150 个字，最多 3 段，命中的词用 <mark> 包起来。
        if highlight:
            search = search.highlight('title', 'body',
                                    fragment_size=150,  # 片段大小
                                    number_of_fragments=3,  # 片段数量
                                    pre_tags=['<mark>'],  # 高亮开始标签
                                    post_tags=['</mark>'])  # 高亮结束标签

        # DH: 不返回原文，只要命中的片段。
        search = search.source(False)[start_offset: end_offset]

        results = search.execute()
        # ES 8.x: total 现在是对象 {'value': 123, 'relation': 'eq'}
        # DH: ES 8 里总数是个对象，要取 value。
        hits_total = results['hits']['total']
        hits = hits_total['value'] if isinstance(hits_total, dict) else hits_total
        raw_results = []
        # DH: 把每条结果转成 Haystack 认识的结果对象。
        for raw_result in results['hits']['hits']:
            app_label = 'blog'
            model_name = 'Article'
            additional_fields = {}

            # 添加高亮内容
            # DH: 有高亮内容就一起带上，前端显示用。
            if highlight and 'highlight' in raw_result:
                highlighted = {}
                if 'title' in raw_result['highlight']:
                    highlighted['title'] = raw_result['highlight']['title']
                if 'body' in raw_result['highlight']:
                    highlighted['body'] = raw_result['highlight']['body']

                if highlighted:
                    additional_fields['highlighted'] = highlighted

            result_class = SearchResult

            result = result_class(
                app_label,
                model_name,
                raw_result['_id'],
                raw_result['_score'],
                **additional_fields)
            raw_results.append(result)
        facets = {}
        # DH: 推荐词和原词不一样时，说明是猜的，给前端提示一下。
        spelling_suggestion = None if query_string == suggestion else suggestion

        # DH: 返回结果、总数和推荐词。
        return {
            'results': raw_results,
            'hits': hits,
            'facets': facets,
            'spelling_suggestion': spelling_suggestion,
        }


# DH: 把 Django 的查询条件转成 ES 能懂的写法，顺便清理用户输入里的特殊字符。
class ElasticSearchQuery(BaseSearchQuery):
    # DH: 把时间转成 ES 用的字符串格式。
    def _convert_datetime(self, date):
        if hasattr(date, 'hour'):
            return force_str(date.strftime('%Y%m%d%H%M%S'))
        else:
            return force_str(date.strftime('%Y%m%d000000'))

    # DH: 用户输入里有特殊字符时，给整词加引号，防止把查询语句搞乱。
    def clean(self, query_fragment):
        """
        Provides a mechanism for sanitizing user input before presenting the
        value to the backend.

        Whoosh 1.X differs here in that you can no longer use a backslash
        to escape reserved characters. Instead, the whole word should be
        quoted.
        """
        words = query_fragment.split()
        cleaned_words = []

        for word in words:
            if word in self.backend.RESERVED_WORDS:
                word = word.replace(word, word.lower())

            for char in self.backend.RESERVED_CHARACTERS:
                if char in word:
                    word = "'%s'" % word
                    break

            cleaned_words.append(word)

        return ' '.join(cleaned_words)

    # DH: 直接用查询字符串，不再拼字段条件。
    def build_query_fragment(self, field, filter_type, value):
        return value.query_string

    # DH: 取结果条数。
    def get_count(self):
        results = self.get_results()
        return len(results) if results else 0

    # DH: 把推荐词交给上层。
    def get_spelling_suggestion(self, preferred_query=None):
        return self._spelling_suggestion

    # DH: 沿用父类的参数，暂时不改。
    def build_params(self, spelling_query=None):
        kwargs = super(ElasticSearchQuery, self).build_params(spelling_query=spelling_query)
        return kwargs


# DH: 搜索表单，多了一个“要不要给推荐词”的开关。
class ElasticSearchModelSearchForm(ModelSearchForm):

    # DH: 如果参数里 is_suggest 不是 no，就开启推荐词。
    def search(self):
        # 是否建议搜索
        self.searchqueryset.query.backend.is_suggest = self.data.get("is_suggest") != "no"
        sqs = super().search()
        return sqs


# DH: 把后端和查询类绑在一起，Haystack 用这个入口。
class ElasticSearchEngine(BaseEngine):
    backend = ElasticSearchBackend
    query = ElasticSearchQuery
