# DH: 这个文件是插件钩子的“电话总机”：插件先登记，主程序需要时按名字调用。

import logging

logger = logging.getLogger(__name__)

# DH: 用一个字典存所有钩子，键是钩子名，值是登记过的处理代码。
_hooks = {}


# DH: 登记一个钩子：名字没出现过就新建一个列表，然后把处理代码加进去。
def register(hook_name: str, callback: callable):
    """
    注册一个钩子回调。
    """
    if hook_name not in _hooks:
        _hooks[hook_name] = []
    _hooks[hook_name].append(callback)
    # DH: 调试时能看到谁挂了哪个钩子。
    logger.debug(f"Registered hook '{hook_name}' with callback '{callback.__name__}'")


# DH: 执行一种“动作型”钩子，登记了几个就按顺序执行几个。
def run_action(hook_name: str, *args, **kwargs):
    """
    执行一个 Action Hook。
    它会按顺序执行所有注册到该钩子上的回调函数。
    """
    if hook_name in _hooks:
        logger.debug(f"Running action hook '{hook_name}'")
        for callback in _hooks[hook_name]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                # DH: 某个插件出错只记日志，不能让整个页面跟着崩。
                logger.error(f"Error running action hook '{hook_name}' callback '{callback.__name__}': {e}", exc_info=True)


# DH: 执行“过滤型”钩子，把值一层层传下去，每个插件改完再交给下一个。
def apply_filters(hook_name: str, value, *args, **kwargs):
    """
    执行一个 Filter Hook。
    它会把 value 依次传递给所有注册的回调函数进行处理。
    """
    if hook_name in _hooks:
        logger.debug(f"Applying filter hook '{hook_name}'")
        for callback in _hooks[hook_name]:
            try:
                value = callback(value, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error applying filter hook '{hook_name}' callback '{callback.__name__}': {e}", exc_info=True)
    # DH: 返回最后一个插件处理完的结果。
    return value
