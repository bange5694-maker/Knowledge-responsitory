# HJJ: Django管理命令 - 同步用户头像
# 通过 python manage.py sync_user_avatar 执行
# 将所有OAuth用户的远程头像下载到本地静态文件目录

import requests
from django.core.management.base import BaseCommand
from django.templatetags.static import static

from djangoblog.utils import save_user_avatar
from oauth.models import OAuthUser
from oauth.oauthmanager import get_manager_by_type


class Command(BaseCommand):
    # HJJ: 命令帮助信息
    help = 'sync user avatar'

    def test_picture(self, url):
        """
        HJJ: 测试图片URL是否可访问
        
        参数:
            url: str - 图片URL
        返回:
            bool - URL可访问返回True，否则返回False
        """
        try:
            if requests.get(url, timeout=2).status_code == 200:
                return True
        except:
            pass
        return False

    def handle(self, *args, **options):
        """
        HJJ: 命令入口方法
        
        执行流程：
        1. 遍历所有OAuth用户
        2. 检查用户头像URL状态
        3. 若远程头像不可用或为默认头像，尝试重新获取或重置为默认
        
        参数:
            *args: 位置参数（暂未使用）
            **options: 关键字参数（暂未使用）
        返回:
            无
        """
        # HJJ: 获取静态文件根路径前缀
        static_url = static("../")
        
        # HJJ: 获取所有OAuth认证用户
        users = OAuthUser.objects.all()
        self.stdout.write(f'开始同步{len(users)}个用户头像')
        
        for u in users:
            self.stdout.write(f'开始同步:{u.nickname}')
            url = u.picture
            
            if url:
                # HJJ: 判断是否是本地静态文件路径
                if url.startswith(static_url):
                    # HJJ: 测试本地头像文件是否存在
                    if self.test_picture(url):
                        continue  # HJJ: 头像有效，跳过
                    else:
                        # HJJ: 头像文件丢失，尝试从第三方重新获取
                        if u.metadata:
                            manage = get_manager_by_type(u.type)
                            url = manage.get_picture(u.metadata)
                            url = save_user_avatar(url)
                        else:
                            # HJJ: 无第三方数据，使用默认头像
                            url = static('blog/img/avatar.png')
                else:
                    # HJJ: 远程头像URL，下载到本地
                    url = save_user_avatar(url)
            else:
                # HJJ: 无头像记录，设置为默认头像
                url = static('blog/img/avatar.png')
            
            if url:
                self.stdout.write(
                    f'结束同步:{u.nickname}.url:{url}')
                u.picture = url
                u.save()
        
        self.stdout.write('结束同步')