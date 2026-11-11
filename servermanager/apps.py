# LZH: 模块功能：servermanager 应用的 AppConfig 配置，向 Django 注册该应用。

from django.apps import AppConfig


# LZH: 应用配置类：声明 servermanager 应用的注册名，Django 启动时据此加载模型、后台与 URL 配置。
class ServermanagerConfig(AppConfig):
    name = 'servermanager'
