# LZH: 模块功能：微信公众号机器人（WeRoBot）入口，处理文章检索、分类目录、最新文章、帮助
# LZH: 等命令，支持管理员命令执行，其余消息交给 ChatGPT 兜底回复。
# LZH: 会话存储优先使用缓存（MemcacheStorage），缓存不可用时退化为本地文件存储。

import logging
import os
import re

import jsonpickle
from django.conf import settings
from werobot import WeRoBot
from werobot.replies import ArticlesReply, Article
from werobot.session.filestorage import FileStorage

from djangoblog.utils import get_sha256
from servermanager.api.blogapi import BlogApi
from servermanager.api.commonapi import ChatGPT, CommandHandler
from .MemcacheStorage import MemcacheStorage

# LZH: 机器人实例：token 从环境变量读取（默认 'lylinux'），开启会话以支持多轮对话
# LZH: （管理员登录、命令二次确认等流程依赖会话）。
robot = WeRoBot(token=os.environ.get('DJANGO_WEROBOT_TOKEN')
                      or 'lylinux', enable_session=True)
# LZH: 会话存储选择：先探测缓存是否可用，可用则把 session 存入缓存。
memstorage = MemcacheStorage()
if memstorage.is_available:
    robot.config['SESSION_STORAGE'] = memstorage
else:
    # LZH: 缓存不可用时的兜底方案：清理上次遗留的会话文件，改用本地文件存储。
    if os.path.exists(os.path.join(settings.BASE_DIR, 'werobot_session')):
        os.remove(os.path.join(settings.BASE_DIR, 'werobot_session'))
    robot.config['SESSION_STORAGE'] = FileStorage(filename='werobot_session')

# LZH: 全局单例：博客查询接口与命令处理器，避免每条消息都重复构造。
blogapi = BlogApi()
cmd_handler = CommandHandler()
logger = logging.getLogger(__name__)


# LZH: 方法说明：把文章对象列表转换成微信图文卡片回复。
# LZH: 参数：articles — Article 对象列表；message — 触发本次回复的微信消息；
# LZH: 返回：ArticlesReply，可携带多张图文卡片的回复对象；异常：文章无正文时不影响后续处理。
def convert_to_article_reply(articles, message):
    reply = ArticlesReply(message=message)
    from blog.templatetags.blog_tags import truncatechars_content
    for post in articles:
        # LZH: 从文章正文中提取第一张图片（png/jpg）作为卡片缩略图，找不到则留空。
        imgs = re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', post.body)
        imgurl = ''
        if imgs:
            imgurl = imgs[0]
        # LZH: 每条文章生成一张卡片：标题、摘要（截断正文）、缩略图、原文链接。
        article = Article(
            title=post.title,
            description=truncatechars_content(post.body),
            img=imgurl,
            url=post.get_full_url()
        )
        reply.add_article(article)
    return reply


# LZH: 命令：?关键字 —— 以问号开头视为关键词检索，返回图文卡片列表；无结果时回文本提示。
@robot.filter(re.compile(r"^\?.*"))
def search(message, session):
    s = message.content
    # LZH: 去掉开头的 '?' 得到检索关键词。
    searchstr = str(s).replace('?', '')
    result = blogapi.search_articles(searchstr)
    if result:
        # LZH: 检索结果是带评分的结果对象，取其中的 .object 即真实文章对象。
        articles = list(map(lambda x: x.object, result))
        reply = convert_to_article_reply(articles, message)
        return reply
    else:
        return '没有找到相关文章。'


# LZH: 命令：category —— 返回全部文章分类目录，分类名以逗号拼接。
@robot.filter(re.compile(r'^category\s*$', re.I))
def category(message, session):
    categorys = blogapi.get_category_lists()
    content = ','.join(map(lambda x: x.name, categorys))
    return '所有文章分类目录：' + content


# LZH: 命令：recent —— 返回最新文章列表（最多 8 篇）的图文卡片。
@robot.filter(re.compile(r'^recent\s*$', re.I))
def recents(message, session):
    articles = blogapi.get_recent_articles()
    if articles:
        reply = convert_to_article_reply(articles, message)
        return reply
    else:
        return "暂时还没有文章"


# LZH: 命令：help —— 返回机器人支持的命令清单与用法说明。
@robot.filter(re.compile('^help$', re.I))
def help(message, session):
    return '''欢迎关注!
            默认会与图灵机器人聊天~~
        你可以通过下面这些命令来获得信息
        ?关键字搜索文章.
        如?python.
        category获得文章分类目录及文章数.
        category-***获得该分类目录文章
        如category-python
        recent获得最新文章
        help获得帮助.
        weather:获得天气
        如weather:西安
        idcard:获得身份证信息
        如idcard:61048119xxxxxxxxxx
        music:音乐搜索
        如music:阴天快乐
        PS:以上标点符号都不支持中文标点~~
        '''


# LZH: 命令：weather:城市 —— 天气查询占位实现，当前固定返回 "建设中..."。
@robot.filter(re.compile(r'^weather\:.*$', re.I))
def weather(message, session):
    return "建设中..."


# LZH: 命令：idcard:号码 —— 身份证查询占位实现，当前固定返回 "建设中..."。
@robot.filter(re.compile(r'^idcard\:.*$', re.I))
def idcard(message, session):
    return "建设中..."


# LZH: 默认处理器：所有未被上面过滤器命中的消息都进入 MessageHandler，
# LZH: 由其根据会话状态决定是管理员命令流程还是 ChatGPT 聊天。
@robot.handler
def echo(message, session):
    handler = MessageHandler(message, session)
    return handler.handler()


# LZH: 消息处理器：封装单条消息的处理上下文，负责会话状态的恢复与按状态分发回复。
class MessageHandler:
    # LZH: 方法说明：构造处理器，恢复当前用户的会话状态。
    # LZH: 参数：message — 微信消息对象；session — WeRoBot 会话字典；
    # LZH: 返回：None；异常：会话数据无法解析时内部捕获，回退为默认用户状态（普通用户）。
    def __init__(self, message, session):
        userid = message.source
        self.message = message
        self.session = session
        self.userid = userid
        try:
            # LZH: 会话里存的是 jsonpickle 序列化后的字符串，需要反序列化还原对象。
            info = session[userid]
            self.userinfo = jsonpickle.decode(info)
        except Exception as e:
            # LZH: 首次对话或数据损坏：使用全新的默认用户状态。
            userinfo = WxUserInfo()
            self.userinfo = userinfo

    # LZH: 属性说明：当前会话是否处于管理员模式。
    @property
    def is_admin(self):
        return self.userinfo.isAdmin

    # LZH: 属性说明：管理员密码是否已通过校验。
    @property
    def is_password_set(self):
        return self.userinfo.isPasswordSet

    # LZH: 方法说明：把当前用户状态序列化后写回会话，保证多轮对话状态一致。
    # LZH: 参数：无；返回：None；异常：序列化失败时向上抛出。
    def save_session(self):
        info = jsonpickle.encode(self.userinfo)
        self.session[self.userid] = info

    # LZH: 方法说明：消息分发主逻辑，按会话状态依次判断管理员退出、进入管理模式、
    # LZH: 密码校验、命令执行，最后兜底交给 ChatGPT。
    # LZH: 参数：无（使用实例上的 message/session/userinfo）；返回：str 或 ArticlesReply；
    # LZH: 异常：下游接口异常向上抛出。
    def handler(self):
        info = self.message.content

        # LZH: 分支一：管理员发送 EXIT —— 清空会话状态并退出管理员模式。
        if self.userinfo.isAdmin and info.upper() == 'EXIT':
            self.userinfo = WxUserInfo()
            self.save_session()
            return "退出成功"
        # LZH: 分支二：发送 ADMIN —— 进入管理员模式，先要求输入管理员密码。
        if info.upper() == 'ADMIN':
            self.userinfo.isAdmin = True
            self.save_session()
            return "输入管理员密码"
        # LZH: 分支三：已进入管理员模式但密码还未验证 —— 用双重 SHA256 与 settings.WXADMIN 比对。
        if self.userinfo.isAdmin and not self.userinfo.isPasswordSet:
            passwd = settings.WXADMIN
            # LZH: 测试环境使用固定密码 '123'，便于自动化测试。
            if settings.TESTING:
                passwd = '123'
            if passwd.upper() == get_sha256(get_sha256(info)).upper():
                # LZH: 校验通过：标记密码已验证，进入命令输入阶段。
                self.userinfo.isPasswordSet = True
                self.save_session()
                return "验证通过,请输入命令或者要执行的命令代码:输入helpme获得帮助"
            else:
                # LZH: 校验失败：累计失败次数，超过 3 次直接清空会话（防止暴力破解）。
                if self.userinfo.Count >= 3:
                    self.userinfo = WxUserInfo()
                    self.save_session()
                    return "超过验证次数"
                self.userinfo.Count += 1
                self.save_session()
                return "验证失败，请重新输入管理员密码:"
        # LZH: 分支四：管理员已通过校验 —— 进入命令执行阶段。
        if self.userinfo.isAdmin and self.userinfo.isPasswordSet:
            # LZH: 上一条命令已暂存且本次回复 Y，视为二次确认，立即执行该命令。
            if self.userinfo.Command != '' and info.upper() == 'Y':
                return cmd_handler.run(self.userinfo.Command)
            else:
                # LZH: 发送 HELPME —— 返回数据库中配置的命令帮助列表。
                if info.upper() == 'HELPME':
                    return cmd_handler.get_help()
                # LZH: 其他输入先暂存为待执行命令，等用户回复 Y 再执行，避免误操作。
                self.userinfo.Command = info
                self.save_session()
                return "确认执行: " + info + " 命令?"

        # LZH: 兜底：普通用户的消息交给 ChatGPT 生成回复。
        return ChatGPT.chat(info)


# LZH: 微信用户会话状态：保存管理员身份、密码验证状态、失败次数与待执行命令。
class WxUserInfo():
    # LZH: 方法说明：初始化默认状态——非管理员、密码未验证、失败次数为 0、无待执行命令。
    # LZH: 参数：无；返回：None。
    def __init__(self):
        self.isAdmin = False
        self.isPasswordSet = False
        self.Count = 0
        self.Command = ''
