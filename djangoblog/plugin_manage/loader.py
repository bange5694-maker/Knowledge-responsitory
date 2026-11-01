# DH: 这个文件负责把 plugins 目录下的插件一个个找出来、加载进来，网站启动时跑一次。

import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# 全局插件注册表
# DH: 加载成功的插件都放这个列表里，后面按名字查。
_loaded_plugins = []

# DH: 按配置文件里写的启用列表，挨个去 plugins 目录找 plugin.py。
def load_plugins():
    """
    Dynamically loads and initializes plugins from the 'plugins' directory.
    This function is intended to be called when the Django app registry is ready.
    """
    global _loaded_plugins
    # DH: 先清空，避免重复加载。
    _loaded_plugins = []

    for plugin_name in settings.ACTIVE_PLUGINS:
        plugin_path = os.path.join(settings.PLUGINS_DIR, plugin_name)
        # DH: 只处理目录存在、而且里面有 plugin.py 的，其他的跳过。
        if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, 'plugin.py')):
            try:
                # 导入插件模块
                # DH: 动态导入插件的 plugin.py，路径是 plugins.插件名.plugin。
                plugin_module = __import__(f'plugins.{plugin_name}.plugin', fromlist=['plugin'])

                # 获取插件实例
                # DH: 插件里必须有一个叫 plugin 的对象，没有就说明写得不规范。
                if hasattr(plugin_module, 'plugin'):
                    plugin_instance = plugin_module.plugin
                    _loaded_plugins.append(plugin_instance)
                    # DH: 加载成功就记下来，启动日志里能看到。
                    logger.info(f"Successfully loaded plugin: {plugin_name} - {plugin_instance.PLUGIN_NAME}")
                else:
                    logger.warning(f"Plugin {plugin_name} does not have 'plugin' instance")

            except ImportError as e:
                # DH: 导入失败只记日志，别让一个插件坏了整个网站。
                logger.error(f"Failed to import plugin: {plugin_name}", exc_info=e)
            except AttributeError as e:
                logger.error(f"Failed to get plugin instance: {plugin_name}", exc_info=e)
            except Exception as e:
                logger.error(f"Unexpected error loading plugin: {plugin_name}", exc_info=e)

    return _loaded_plugins

# DH: 把已经加载的插件列表交出去。
def get_loaded_plugins():
    """获取所有已加载的插件"""
    return _loaded_plugins

# DH: 按名字找插件，找不到就返回 None。
def get_plugin_by_name(plugin_name):
    """根据名称获取插件"""
    for plugin in _loaded_plugins:
        if plugin.plugin_slug == plugin_name:
            return plugin
    return None

# DH: 按 slug 找插件，找不到就返回 None。
def get_plugin_by_slug(plugin_slug):
    """根据slug获取插件"""
    for plugin in _loaded_plugins:
        if plugin.plugin_slug == plugin_slug:
            return plugin
    return None

# DH: 把所有插件的信息整理成列表，给后台或调试用。
def get_plugins_info():
    """获取所有插件的信息"""
    return [plugin.get_plugin_info() for plugin in _loaded_plugins]

# DH: 找出能在指定位置显示的插件，比如侧边栏、文章底部。
def get_plugins_by_position(position):
    """获取支持指定位置的插件"""
    return [plugin for plugin in _loaded_plugins if position in plugin.SUPPORTED_POSITIONS] 
