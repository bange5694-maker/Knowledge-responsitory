# ZYH: 模块功能：accounts 应用的配置类，向 Django 声明应用名称与显示名称。

from django.apps import AppConfig


# ZYH: 账户应用配置；name 必须与应用的 Python 包名一致，Django 启动时据此加载。
class AccountsConfig(AppConfig):
    name = 'accounts'
