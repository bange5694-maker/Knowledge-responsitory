# DH: 这个文件是 djangoblog 应用的配置，Django 启动时会先读这里。

from django.apps import AppConfig


# DH: 应用的配置类，名字要和 Django 里注册的应用对得上。
class DjangoblogAppConfig(AppConfig):
    # DH: 主键用大整数自增，跟 Django 新版本的默认做法一致。
    default_auto_field = 'django.db.models.BigAutoField'
    # DH: 应用名，就是文件夹名。
    name = 'djangoblog'

    # DH: Django 启动时会自动调用 ready()，这里把插件都加载进来，不然插件不会生效。
    def ready(self):
        super().ready()
        # DH: 导入插件加载器，然后执行加载。
        # Import and load plugins here
        from .plugin_manage.loader import load_plugins
        load_plugins() 
