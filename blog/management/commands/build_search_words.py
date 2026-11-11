# HJJ: Django管理命令 - 生成搜索关键词列表
# 通过 python manage.py build_words 执行
# 收集所有标签和分类名称，用于搜索引擎词库扩展

from django.core.management.base import BaseCommand

from blog.models import Tag, Category


# HJJ: TODO 后续可增加参数支持（如输出格式、文件路径等）
class Command(BaseCommand):
    # HJJ: 命令帮助信息
    help = 'build search words'

    def handle(self, *args, **options):
        """
        HJJ: 命令入口方法
        
        执行流程：
        1. 从数据库中查询所有标签名称
        2. 从数据库中查询所有分类名称
        3. 合并去重后输出到控制台
        
        参数:
            *args: 位置参数（暂未使用）
            **options: 关键字参数（暂未使用）
        返回:
            无（结果直接打印到标准输出）
        """
        # HJJ: 合并标签和分类的名称集合，自动去重
        datas = set(
            [t.name for t in Tag.objects.all()] +
            [t.name for t in Category.objects.all()]
        )
        
        # HJJ: 每行一个关键词输出到控制台
        # 可用于导入IK分词器的自定义词库
        print('\n'.join(datas))