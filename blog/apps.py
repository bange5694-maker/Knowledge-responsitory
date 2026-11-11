# HJJ: 博客应用配置模块，负责应用启动时的初始化工作，
# HJJ: 包括Elasticsearch和Whoosh两种搜索引擎的索引状态检查与创建

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class BlogConfig(AppConfig):
    # HJJ: 指定该配置对应的Django应用名称
    name = 'blog'

    def ready(self):
        """
        HJJ: Django应用就绪时的回调方法，用于执行启动初始化逻辑
        参数: 无
        返回: 无
        异常: 无（内部异常已被捕获并记录日志）
        """
        # HJJ: 检查并创建搜索索引（如果需要）
        self.check_search_index()

    def check_search_index(self):
        """
        HJJ: 检查Elasticsearch和Whoosh两种搜索引擎的索引是否存在，
        HJJ: 若不存在则尝试创建空索引（ES）或记录日志等待首次搜索自动创建（Whoosh）
        参数: 无
        返回: 无
        异常: 捕获所有异常并记录警告日志，不中断应用启动流程
        """
        from django.conf import settings

        # HJJ: 1. 检查Elasticsearch索引
        if hasattr(settings, 'ELASTICSEARCH_DSL'):
            try:
                from blog.documents import ELASTICSEARCH_ENABLED, ArticleDocumentManager
                if ELASTICSEARCH_ENABLED:
                    from elasticsearch import Elasticsearch
                    es_config = settings.ELASTICSEARCH_DSL['default']
                    # HJJ: 建立Elasticsearch客户端连接，禁用SSL证书验证
                    es = Elasticsearch(hosts=[es_config['hosts']], verify_certs=False)

                    # HJJ: 检查blog索引是否存在，不存在则通过ArticleDocumentManager创建空索引
                    if not es.indices.exists(index='blog'):
                        logger.info("Elasticsearch blog index not found, creating empty index...")
                        manager = ArticleDocumentManager()
                        logger.info("Elasticsearch blog index created successfully")
                    else:
                        logger.debug("Elasticsearch blog index already exists")
            except Exception as e:
                logger.warning(f"Failed to check/create Elasticsearch index: {e}")

        # HJJ: 2. 检查Whoosh索引
        haystack_engine = settings.HAYSTACK_CONNECTIONS.get('default', {}).get('ENGINE', '')
        if 'whoosh' in haystack_engine.lower():
            try:
                import os
                whoosh_path = settings.HAYSTACK_CONNECTIONS['default'].get('PATH')
                if whoosh_path and not os.path.exists(whoosh_path):
                    # HJJ: Whoosh索引目录不存在，记录日志，首次搜索时会自动创建
                    logger.info(f"Whoosh index directory not found at {whoosh_path}, will be created on first search")
                elif whoosh_path and os.path.exists(whoosh_path):
                    # HJJ: 检查索引目录下是否有段文件(.seg)或写锁文件(_MAIN_WRITELOCK)，判断是否为空索引
                    index_files = [f for f in os.listdir(whoosh_path) if f.endswith('.seg') or f == '_MAIN_WRITELOCK']
                    if not index_files:
                        logger.info("Whoosh index directory exists but empty, will be initialized on first search")
                    else:
                        logger.debug("Whoosh index already exists")
            except Exception as e:
                logger.warning(f"Failed to check Whoosh index: {e}")