# XJN: 模块功能：comments 应用的 AppConfig 配置，向 Django 声明应用名称与默认配置类。
from django.apps import AppConfig


# XJN: 评论应用配置类：注册 comments 应用，供 Django 启动时加载模型、信号与模板标签。
# XJN: 入参：Django 按 INSTALLED_APPS 中的 'comments' 自动实例化。
# XJN: 返回值：AppConfig 实例，name 属性指定应用的点路径。
class CommentsConfig(AppConfig):
    # XJN: 应用点路径，必须与 INSTALLED_APPS 中的注册名一致。
    name = 'comments'
