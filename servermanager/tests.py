# LZH: 模块功能：servermanager 应用的单元测试，覆盖 ChatGPT 兜底聊天、检索/分类/最新文章命令
# LZH: 以及管理员命令执行流程（进入管理模式、密码验证、命令二次确认、退出）。

from django.test import Client, RequestFactory, TestCase
from django.utils import timezone
from werobot.messages.messages import TextMessage

from accounts.models import BlogUser
from blog.models import Category, Article
from servermanager.api.commonapi import ChatGPT
from .models import commands
from .robot import MessageHandler, CommandHandler
from .robot import search, category, recents


# Create your tests here.

# LZH: 测试用例类：用 Django TestCase 搭建用户/分类/文章数据，验证微信机器人各命令的返回。
class ServerManagerTest(TestCase):
    # LZH: 方法说明：每个测试方法执行前的初始化——构造 HTTP 客户端与请求工厂。
    # LZH: 参数：无；返回：None。
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    # LZH: 测试：ChatGPT 接口能返回非空内容（外部服务不可用时返回错误提示，同样非空）。
    def test_chat_gpt(self):
        content = ChatGPT.chat("你好")
        self.assertIsNotNone(content)

    # LZH: 测试：端到端验证检索、分类、最新文章命令与管理员的命令执行流程。
    def test_validate_comment(self):
        # LZH: 准备数据：创建超级用户、分类与一篇文章，作为命令查询的样本数据。
        user = BlogUser.objects.create_superuser(
            email="liangliangyy1@gmail.com",
            username="liangliangyy1",
            password="liangliangyy1")

        self.client.login(username='liangliangyy1', password='liangliangyy1')

        c = Category()
        c.name = "categoryccc"
        c.save()

        article = Article()
        article.title = "nicetitleccc"
        article.body = "nicecontentccc"
        article.author = user
        article.category = c
        article.type = 'a'
        article.status = 'p'
        article.save()
        # LZH: 构造一条文本消息，依次触发 ?检索、category、recent 三个命令。
        s = TextMessage([])
        s.content = "nice"
        rsp = search(s, None)
        rsp = category(None, None)
        self.assertIsNotNone(rsp)
        rsp = recents(None, None)
        self.assertTrue(rsp != '暂时还没有文章')

        # LZH: 写入一条命令配置，验证 CommandHandler 能按标题找到并执行它。
        cmd = commands()
        cmd.title = "test"
        cmd.command = "ls"
        cmd.describe = "test"
        cmd.save()

        cmdhandler = CommandHandler()
        rsp = cmdhandler.run('test')
        self.assertIsNotNone(rsp)
        # LZH: 构造消息处理器，空会话表示首次对话；随后依次模拟普通消息、确认 Y、
        # LZH: 天气/身份证占位命令、进入管理员模式、输入密码与退出等对话步骤。
        s.source = 'u'
        s.content = 'test'
        msghandler = MessageHandler(s, {})

        # msghandler.userinfo.isPasswordSet = True
        # msghandler.userinfo.isAdmin = True
        msghandler.handler()
        s.content = 'y'
        msghandler.handler()
        s.content = 'idcard:12321233'
        msghandler.handler()
        s.content = 'weather:上海'
        msghandler.handler()
        s.content = 'admin'
        msghandler.handler()
        s.content = '123'
        msghandler.handler()

        s.content = 'exit'
        msghandler.handler()
