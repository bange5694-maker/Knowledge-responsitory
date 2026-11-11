# HJJ: 全局上下文处理器模块
# 为所有模板提供通用的站点配置数据，减少重复查询
# 使用10小时缓存策略优化性能

import logging

from django.utils import timezone

from djangoblog.utils import cache, get_blog_setting
from .models import Category, Article

logger = logging.getLogger(__name__)


def seo_processor(requests):
    """
    HJJ: 全局模板上下文处理器
    向所有模板注入站点配置、导航分类、页面列表等公共数据
    
    参数:
        requests: HttpRequest - Django请求对象
    返回:
        dict - 包含所有模板变量的字典
    """
    key = 'seo_processor'
    value = cache.get(key)
    if value:
        # HJJ: 缓存命中，仅更新动态值（不需要缓存的内容）
        value['SITE_BASE_URL'] = requests.scheme + '://' + requests.get_host() + '/'
        value['CURRENT_YEAR'] = timezone.now().year
        return value
    else:
        # HJJ: 缓存未命中，从数据库加载并设置缓存
        logger.info('set processor cache.')
        setting = get_blog_setting()

        # HJJ: 优化查询：预加载导航分类和独立页面数据
        nav_category_list = Category.objects.all()
        nav_pages = Article.objects.filter(
            type='p',
            status='p'
        )

        value = {
            # HJJ: 站点基本信息
            'SITE_NAME': setting.site_name,
            'SITE_DESCRIPTION': setting.site_description,
            'SITE_SEO_DESCRIPTION': setting.site_seo_description,
            'SITE_KEYWORDS': setting.site_keywords,
            'SITE_BASE_URL': requests.scheme + '://' + requests.get_host() + '/',
            
            # HJJ: 广告配置
            'SHOW_GOOGLE_ADSENSE': setting.show_google_adsense,
            'GOOGLE_ADSENSE_CODES': setting.google_adsense_codes,
            
            # HJJ: 文章摘要截取长度
            'ARTICLE_SUB_LENGTH': setting.article_sub_length,
            
            # HJJ: 导航数据（保持QuerySet惰性求值）
            'nav_category_list': nav_category_list,
            'nav_pages': nav_pages,
            
            # HJJ: 评论配置
            'OPEN_SITE_COMMENT': setting.open_site_comment,
            'COMMENT_NEED_REVIEW': setting.comment_need_review,
            
            # HJJ: 底部备案信息
            'BEIAN_CODE': setting.beian_code,
            "BEIAN_CODE_GONGAN": setting.gongan_beiancode,
            "SHOW_GONGAN_CODE": setting.show_gongan_code,
            
            # HJJ: 统计分析代码
            'ANALYTICS_CODE': setting.analytics_code,
            
            # HJJ: 全局头部/尾部HTML
            "GLOBAL_HEADER": setting.global_header,
            "GLOBAL_FOOTER": setting.global_footer,
            
            # HJJ: 主题配色方案
            "COLOR_SCHEME": setting.color_scheme,
            
            # HJJ: 动态值（每年更新）
            "CURRENT_YEAR": timezone.now().year,
        }
        # HJJ: 设置10小时缓存
        cache.set(key, value, 60 * 60 * 10)
        return value