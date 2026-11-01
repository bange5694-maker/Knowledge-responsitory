# DH: 这个文件负责把新文章的网址推给百度，让百度收录得快一点。

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# DH: 通知百度蜘蛛的类，目前只用到百度这一个。
class SpiderNotify():
    # DH: 把网址列表拼成一行一个，整段提交给百度。
    @staticmethod
    def baidu_notify(urls):
        try:
            data = '\n'.join(urls)
            result = requests.post(settings.BAIDU_NOTIFY_URL, data=data)
            # DH: 记一下百度返回的内容，方便排查。
            logger.info(result.text)
        except Exception as e:
            # DH: 推送失败只记日志，不影响正常发文章。
            logger.error(e)

    # DH: 对外只留这一个入口，以后要加别的搜索引擎也在这里改。
    @staticmethod
    def notify(url):
        SpiderNotify.baidu_notify(url)
