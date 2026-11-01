#!/usr/bin/env python
# encoding: utf-8
# DH: 这个文件放全站通用的常量：缓存多久过期、缓存键怎么命名、HTTP 状态码和分页默认值。改这些配置时来这里找。

"""
Django Blog 全局常量定义
包含缓存超时时间、缓存键模板等配置
"""


# ===== 缓存过期时间（秒）=====
# DH: 缓存过期时间都写在这里，写成 60 * 5 这种样子，一眼能看出是 5 分钟，不用自己算秒数。
class CacheTimeout:
    """
    缓存超时时间常量
    集中管理所有缓存过期时间，便于统一调整缓存策略
    """
    # 分钟级
    MINUTE_1 = 60
    MINUTE_5 = 60 * 5
    MINUTE_10 = 60 * 10
    MINUTE_30 = 60 * 30

    # 小时级
    HOUR_1 = 60 * 60
    HOUR_2 = 60 * 60 * 2
    HOUR_10 = 60 * 60 * 10
    HOUR_24 = 60 * 60 * 24

    # 天级
    DAY_7 = 60 * 60 * 24 * 7
    DAY_30 = 60 * 60 * 24 * 30

    # 默认缓存时间
    # DH: 默认缓存 10 小时，和 settings 里页面的缓存时间保持一致。
    DEFAULT = HOUR_10  # 10小时


# ===== 缓存键前缀 =====
# DH: 缓存键的模板。键名统一写在这里，代码里用的时候不怕拼错，以后要改也只用改这一处。
class CacheKey:
    """
    缓存键模板
    使用字符串格式化模板，避免缓存键拼写错误
    """
    # 文章相关
    ARTICLE_COMMENTS = 'article_comments_{article_id}'
    ARTICLE_NEXT = 'article_next_{article_id}'
    ARTICLE_PREV = 'article_prev_{article_id}'
    ARTICLE_CATEGORY_TREE = 'article_category_tree_{article_id}'

    # 列表页缓存
    INDEX_LIST = 'index_{page}'
    CATEGORY_LIST = 'category_list_{name}_{page}'
    TAG_LIST = 'tag_{name}_{page}'
    AUTHOR_LIST = 'author_{name}_{page}'
    ARCHIVES = 'archives'

    # 分类和标签
    CATEGORY_TREE = 'category_tree_{category_id}'
    SUB_CATEGORIES = 'sub_categories_{category_id}'
    TAG_ARTICLE_COUNT = 'tag_article_count_{tag_id}'

    # 全局设置
    BLOG_SETTINGS = 'blog_settings'
    CURRENT_SITE = 'current_site'
    SIDEBAR = 'sidebar_{type}'

    # 侧边栏相关
    SIDEBAR_LATEST_ARTICLES = 'sidebar_latest_articles'
    SIDEBAR_HOT_ARTICLES = 'sidebar_hot_articles'
    SIDEBAR_LATEST_COMMENTS = 'sidebar_latest_comments'


# ===== HTTP 状态码 =====
# DH: 常用的 HTTP 状态码，给接口返回结果的时候用，省得在代码里直接写数字。
class HttpStatus:
    """HTTP 状态码常量"""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404

    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


# ===== 分页配置 =====
# DH: 分页的默认值：一页 10 条，最多 100 条，页码参数叫 page。
class Pagination:
    """分页相关常量"""
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    PAGE_QUERY_PARAM = 'page'
