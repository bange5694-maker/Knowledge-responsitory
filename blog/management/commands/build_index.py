# HJJ: Django管理命令 - 构建Elasticsearch搜索索引
# 通过 python manage.py build_index 执行
# 重建文章搜索索引和性能监控索引

from django.core.management.base import BaseCommand

from blog.documents import ElapsedTimeDocument, ArticleDocumentManager, ElaspedTimeDocumentManager, \
    ELASTICSEARCH_ENABLED


# HJJ: TODO 后续可增加命令行参数支持（如指定重建范围、索引名称等）
class Command(BaseCommand):
    # HJJ: 命令帮助信息
    help = 'build search index'

    def handle(self, *args, **options):
        """
        HJJ: 命令入口方法
        
        执行流程：
        1. 检查ES是否启用
        2. 创建/重建performance索引（页面性能监控）
        3. 删除并重建blog索引（文章全文搜索）
        
        参数:
            *args: 位置参数（暂未使用）
            **options: 关键字参数（暂未使用）
        返回:
            无
        """
        if ELASTICSEARCH_ENABLED:
            # HJJ: 创建或更新performance索引（用于存储页面响应耗时数据）
            ElaspedTimeDocumentManager.build_index()
            
            # HJJ: 初始化ElapsedTimeDocument索引映射
            manager = ElapsedTimeDocument()
            manager.init()
            
            # HJJ: 重建文章搜索索引（先删除旧索引，再全量重建）
            manager = ArticleDocumentManager()
            manager.delete_index()  # HJJ: 删除旧的blog索引
            manager.rebuild()       # HJJ: 从数据库全量同步文章数据到ES