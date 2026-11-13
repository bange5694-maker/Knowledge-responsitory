# HJJ: Elasticsearch文档映射与管理模块
# 定义博客文章(ArticleDocument)和性能监控(ElapsedTimeDocument)的ES索引结构
# 支持IK中文分词、GeoIP地理定位、User-Agent解析等功能

import time

import elasticsearch.client
from django.conf import settings
from elasticsearch_dsl import Document, InnerDoc, Date, Integer, Long, Text, Object, GeoPoint, Keyword, Boolean
from elasticsearch_dsl.connections import connections

from blog.models import Article

# HJJ: 检测是否配置了Elasticsearch，未配置则不启用ES相关功能
ELASTICSEARCH_ENABLED = hasattr(settings, 'ELASTICSEARCH_DSL')

if ELASTICSEARCH_ENABLED:
    from elasticsearch import Elasticsearch

    es_config = settings.ELASTICSEARCH_DSL['default']

    # HJJ: 处理hosts配置，确保每个地址都有scheme前缀
    hosts = es_config['hosts']
    if isinstance(hosts, str):
        # HJJ: 字符串格式的hosts，自动补全http://
        if not hosts.startswith(('http://', 'https://')):
            hosts = f'http://{hosts}'
        hosts = [hosts]
    elif isinstance(hosts, list):
        # HJJ: 列表格式的hosts，逐个处理
        processed_hosts = []
        for host in hosts:
            if not host.startswith(('http://', 'https://')):
                host = f'http://{host}'
            processed_hosts.append(host)
        hosts = processed_hosts

    # HJJ: ES连接配置（动态适配多种认证方式）
    es_params = {
        'hosts': hosts,
        'verify_certs': es_config.get('verify_certs', False),
    }

    # HJJ: 支持用户名密码认证（ES 8.x默认启用安全特性）
    if 'username' in es_config and 'password' in es_config:
        es_params['basic_auth'] = (es_config['username'], es_config['password'])

    # HJJ: 支持API Key认证
    if 'api_key' in es_config:
        es_params['api_key'] = es_config['api_key']

    # HJJ: 支持CA证书认证
    if 'ca_certs' in es_config:
        es_params['ca_certs'] = es_config['ca_certs']

    # HJJ: 支持客户端双向证书认证
    if 'client_cert' in es_config and 'client_key' in es_config:
        es_params['client_cert'] = es_config['client_cert']
        es_params['client_key'] = es_config['client_key']

    # HJJ: 创建ES客户端连接
    es = Elasticsearch(**es_params)
    connections.create_connection(**es_params)

    # HJJ: 设置GeoIP pipeline，用于IP地址地理位置解析
    try:
        es.ingest.get_pipeline(id='geoip')
    except elasticsearch.exceptions.NotFoundError:
        es.ingest.put_pipeline(id='geoip', body={
            "description": "Add geoip info",
            "processors": [
                {
                    "geoip": {
                        "field": "ip"
                    }
                }
            ]
        })


class GeoIp(InnerDoc):
    # HJJ: GeoIP地理位置信息内部文档类型
    continent_name = Keyword()
    country_iso_code = Keyword()
    country_name = Keyword()
    location = GeoPoint()


class UserAgentBrowser(InnerDoc):
    # HJJ: 浏览器信息内部文档类型
    Family = Keyword()
    Version = Keyword()


class UserAgentOS(UserAgentBrowser):
    # HJJ: 操作系统信息，继承浏览器结构（Family/Version）
    pass


class UserAgentDevice(InnerDoc):
    # HJJ: 设备信息内部文档类型
    Family = Keyword()
    Brand = Keyword()
    Model = Keyword()


class UserAgent(InnerDoc):
    # HJJ: 完整的User-Agent信息聚合文档
    browser = Object(UserAgentBrowser, required=False)
    os = Object(UserAgentOS, required=False)
    device = Object(UserAgentDevice, required=False)
    string = Text()
    is_bot = Boolean()


class ElapsedTimeDocument(Document):
    # HJJ: 页面响应耗时监控文档映射
    url = Keyword()
    time_taken = Long()
    log_datetime = Date()
    ip = Keyword()
    geoip = Object(GeoIp, required=False)
    useragent = Object(UserAgent, required=False)

    class Index:
        # HJJ: 索引名为'performance'，单分片零副本
        name = 'performance'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }


class ElaspedTimeDocumentManager:
    # HJJ: 性能监控文档管理器，提供索引创建/删除/文档写入等操作

    @staticmethod
    def build_index():
        """HJJ: 创建performance索引（如果不存在）"""
        from elasticsearch import Elasticsearch
        client = Elasticsearch(**es_params)
        res = client.indices.exists(index="performance")
        if not res:
            ElapsedTimeDocument.init()

    @staticmethod
    def delete_index():
        """HJJ: 删除performance索引"""
        from elasticsearch import Elasticsearch
        es = Elasticsearch(**es_params)
        try:
            es.indices.delete(index='performance')
        except elasticsearch.exceptions.NotFoundError:
            pass

    @staticmethod
    def create(url, time_taken, log_datetime, useragent, ip):
        """
        HJJ: 创建一条性能监控记录
        参数:
            url: 请求URL
            time_taken: 响应耗时(毫秒)
            log_datetime: 日志时间
            useragent: user_agents解析后的UA对象
            ip: 客户端IP地址
        返回: 无（文档自动保存到ES）
        """
        ElaspedTimeDocumentManager.build_index()
        # HJJ: 构造UserAgent内部文档
        ua = UserAgent()
        ua.browser = UserAgentBrowser()
        ua.browser.Family = useragent.browser.family
        ua.browser.Version = useragent.browser.version_string

        ua.os = UserAgentOS()
        ua.os.Family = useragent.os.family
        ua.os.Version = useragent.os.version_string

        ua.device = UserAgentDevice()
        ua.device.Family = useragent.device.family
        ua.device.Brand = useragent.device.brand
        ua.device.Model = useragent.device.model
        ua.string = useragent.ua_string
        ua.is_bot = useragent.is_bot

        # HJJ: 创建文档，以毫秒级时间戳作为文档ID
        doc = ElapsedTimeDocument(
            meta={
                'id': int(
                    round(
                        time.time() *
                        1000))
            },
            url=url,
            time_taken=time_taken,
            log_datetime=log_datetime,
            useragent=ua, ip=ip)
        # HJJ: 保存文档时应用GeoIP pipeline进行IP地理定位
        doc.save(pipeline="geoip")


class ArticleDocument(Document):
    # HJJ: 博客文章ES文档映射，支持IK中文分词
    body = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    title = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    author = Object(properties={
        'nickname': Text(analyzer='ik_max_word', search_analyzer='ik_smart'),
        'id': Integer()
    })
    category = Object(properties={
        'name': Text(analyzer='ik_max_word', search_analyzer='ik_smart'),
        'id': Integer()
    })
    tags = Object(properties={
        'name': Text(analyzer='ik_max_word', search_analyzer='ik_smart'),
        'id': Integer()
    })

    pub_time = Date()
    status = Text()
    comment_status = Text()
    type = Text()
    views = Integer()
    article_order = Integer()

    class Index:
        # HJJ: 索引名为'blog'，单分片零副本
        name = 'blog'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }


class ArticleDocumentManager():
    # HJJ: 文章文档管理器，提供索引创建/重建/更新等操作

    def __init__(self):
        # HJJ: 初始化时自动创建blog索引
        self.create_index()

    def create_index(self):
        """HJJ: 创建blog索引（如果不存在）"""
        ArticleDocument.init()

    def delete_index(self):
        """HJJ: 删除blog索引"""
        from elasticsearch import Elasticsearch
        es = Elasticsearch(**es_params)
        try:
            es.indices.delete(index='blog')
        except elasticsearch.exceptions.NotFoundError:
            pass

    def convert_to_doc(self, articles):
        """
        HJJ: 将Django ORM的Article对象列表转换为ES文档对象列表
        参数: articles - QuerySet[Article] 文章查询集
        返回: list[ArticleDocument] ES文档对象列表
        """
        return [
            ArticleDocument(
                meta={
                    'id': article.id},
                body=article.body,
                title=article.title,
                author={
                    'nickname': article.author.username,
                    'id': article.author.id},
                category={
                    'name': article.category.name,
                    'id': article.category.id},
                tags=[
                    {
                        'name': t.name,
                        'id': t.id} for t in article.tags.all()],
                pub_time=article.pub_time,
                status=article.status,
                comment_status=article.comment_status,
                type=article.type,
                views=article.views,
                article_order=article.article_order) for article in articles]

    def rebuild(self, articles=None):
        """
        HJJ: 重建整个blog索引（全量同步）
        参数: articles - 可选，指定要索引的文章列表，默认索引全部文章
        返回: 无
        """
        ArticleDocument.init()
        articles = articles if articles else Article.objects.all()
        docs = self.convert_to_doc(articles)
        for doc in docs:
            doc.save()

    def update_docs(self, docs):
        """
        HJJ: 批量更新文档到ES
        参数: docs - list[ArticleDocument] 待更新的文档列表
        返回: 无
        """
        for doc in docs:
            doc.save()