# LZH: 模块功能：基于 Django 缓存的 WeRoBot 会话存储实现，用于在微信多轮对话中保存
# LZH: 用户会话状态（是否管理员、密码是否已验证、失败次数、待确认执行的命令）。

from werobot.session import SessionStorage
from werobot.utils import json_loads, json_dumps

from djangoblog.utils import cache


# LZH: 会话存储类：继承 WeRoBot 的 SessionStorage，把会话读写代理到 djangoblog.utils.cache。
class MemcacheStorage(SessionStorage):
    # LZH: 方法说明：初始化缓存键前缀与缓存后端。
    # LZH: 参数：prefix — 缓存键前缀，默认 'ws_'，用于隔离微信会话与其他业务缓存；返回：None。
    def __init__(self, prefix='ws_'):
        self.prefix = prefix
        self.cache = cache

    # LZH: 属性说明：探测缓存是否可用——写入 "1" 后立即读回并比对。
    # LZH: 参数：无；返回：bool，True 表示缓存可用；异常：缓存后端异常向上抛出，由调用方兜底。
    @property
    def is_available(self):
        value = "1"
        self.set('checkavaliable', value=value)
        return value == self.get('checkavaliable')

    # LZH: 方法说明：为会话 key 拼接统一前缀，避免与其他业务缓存冲突。
    # LZH: 参数：s — 原始 key（微信用户 openid）；返回：str，带前缀的缓存 key。
    def key_name(self, s):
        return '{prefix}{s}'.format(prefix=self.prefix, s=s)

    # LZH: 方法说明：读取会话，缓存未命中时返回空字典。
    # LZH: 参数：id — 会话标识（openid）；返回：dict，反序列化后的会话数据；
    # LZH: 异常：JSON 解析失败时抛出。
    def get(self, id):
        id = self.key_name(id)
        session_json = self.cache.get(id) or '{}'
        return json_loads(session_json)

    # LZH: 方法说明：写入会话（先序列化为 JSON 再存入缓存）。
    # LZH: 参数：id — 会话标识；value — 会话字典；返回：None。
    def set(self, id, value):
        id = self.key_name(id)
        self.cache.set(id, json_dumps(value))

    # LZH: 方法说明：删除会话，用于退出管理员模式等场景。
    # LZH: 参数：id — 会话标识；返回：None。
    def delete(self, id):
        id = self.key_name(id)
        self.cache.delete(id)
