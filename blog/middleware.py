# HJJ: 在线中间件模块
# 记录每个请求的响应耗时，支持将性能数据写入Elasticsearch
# 同时将页面加载时间注入到HTML模板的占位符中

import logging
import time

from ipware import get_client_ip
from user_agents import parse

from blog.documents import ELASTICSEARCH_ENABLED, ElaspedTimeDocumentManager

logger = logging.getLogger(__name__)


class OnlineMiddleware(object):
    """
    HJJ: 页面性能监控中间件
    计算每个HTTP请求的处理耗时，并将结果记录到Elasticsearch（如果启用）
    同时在响应内容中替换加载时间占位符
    """

    def __init__(self, get_response=None):
        # HJJ: 接收下一个中间件或视图的可调用对象
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        '''
        HJJ: 中间件核心处理方法
        参数:
            request: HttpRequest - Django请求对象
        返回:
            HttpResponse - 经过处理的响应对象
        '''
        # HJJ: 记录请求开始时间
        start_time = time.time()
        
        # HJJ: 调用下一个中间件或视图处理请求
        response = self.get_response(request)
        
        # HJJ: 获取客户端User-Agent字符串
        http_user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # HJJ: 获取客户端真实IP地址
        ip, _ = get_client_ip(request)
        
        # HJJ: 解析User-Agent获取浏览器、操作系统、设备等信息
        user_agent = parse(http_user_agent)
        
        # HJJ: 仅处理非流式响应（避免大文件下载等场景的性能开销）
        if not response.streaming:
            try:
                # HJJ: 计算请求总耗时
                cast_time = time.time() - start_time
                
                # HJJ: 如果启用了Elasticsearch，记录性能数据
                if ELASTICSEARCH_ENABLED:
                    # HJJ: 将耗时转换为毫秒，保留两位小数
                    time_taken = round((cast_time) * 1000, 2)
                    url = request.path
                    from django.utils import timezone
                    
                    # HJJ: 创建ES性能监控文档
                    ElaspedTimeDocumentManager.create(
                        url=url,
                        time_taken=time_taken,
                        log_datetime=timezone.now(),
                        useragent=user_agent,
                        ip=ip)
                
                # HJJ: 替换响应内容中的加载时间占位符 <!!LOAD_TIMES!!>
                # 用于在前端显示页面加载耗时
                response.content = response.content.replace(
                    b'<!!LOAD_TIMES!!>', str.encode(str(cast_time)[:5]))
                    
            except Exception as e:
                # HJJ: 捕获所有异常，防止中间件异常影响正常页面访问
                logger.error("Error OnlineMiddleware: %s" % e)

        return response