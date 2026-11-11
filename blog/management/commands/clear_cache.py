# HJJ: Django管理命令 - 清空所有缓存
# 通过 python manage.py clear_cache 执行
# 清除Redis/Memcached等后端中的所有缓存数据

from django.core.management.base import BaseCommand

from djangoblog.utils import cache


class Command(BaseCommand):
    # HJJ: 命令帮助信息
    help = 'clear the whole cache'

    def handle(self, *args, **options):
        """
        HJJ: 命令入口方法
        
        执行流程：
        1. 调用缓存后端的clear()方法清空所有缓存键
        2. 在控制台输出成功提示
        
        参数:
            *args: 位置参数（暂未使用）
            **options: 关键字参数（暂未使用）
        返回:
            无
        """
        # HJJ: 清空整个缓存（包括侧边栏、SEO处理器等所有缓存数据）
        cache.clear()
        
        # HJJ: 输出绿色成功提示到控制台
        self.stdout.write(self.style.SUCCESS('Cleared cache\n'))