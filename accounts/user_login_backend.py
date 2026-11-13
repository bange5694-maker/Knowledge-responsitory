# ZYH: 模块功能：自定义认证后端，允许用户使用“用户名”或“邮箱”登录。

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


# ZYH: EmailOrUsernameModelBackend 继承 ModelBackend，在默认用户名认证之外补充邮箱认证。
class EmailOrUsernameModelBackend(ModelBackend):
    """
    允许使用用户名或邮箱登录
    """

    # ZYH: 认证入口：username 参数可能是用户名或邮箱，password 为明文密码。
    # ZYH: 认证成功返回用户对象，用户不存在或密码错误返回 None。
    def authenticate(self, request, username=None, password=None, **kwargs):
        # ZYH: 含 @ 时按邮箱查询，否则按用户名查询。
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'username': username}
        try:
            user = get_user_model().objects.get(**kwargs)
            # ZYH: 使用 Django 的 check_password 校验哈希密码，禁止明文比较。
            if user.check_password(password):
                return user
        # ZYH: 查询不到用户时返回 None，交给下一个认证后端处理。
        except get_user_model().DoesNotExist:
            return None

    # ZYH: 根据主键获取用户，供 Django 在会话中恢复登录状态时调用。
    # ZYH: 用户不存在时返回 None。
    def get_user(self, username):
        try:
            return get_user_model().objects.get(pk=username)
        except get_user_model().DoesNotExist:
            return None
