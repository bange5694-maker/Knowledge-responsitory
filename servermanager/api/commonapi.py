# LZH: 模块功能：通用能力接口——ChatGPT 对话（普通消息的兜底回复）与命令处理
# LZH: （从数据库读取命令配置、执行命令、生成帮助文本）。

import logging
import os

import openai

from servermanager.models import commands

logger = logging.getLogger(__name__)

# LZH: 从环境变量读取 OpenAI API Key；未配置时接口调用会失败，由 chat() 捕获后返回友好提示。
openai.api_key = os.environ.get('OPENAI_API_KEY')
# LZH: 若配置了 HTTP_PROXY，则为 openai 设置代理，适配需要走代理的网络环境。
if os.environ.get('HTTP_PROXY'):
    openai.proxy = os.environ.get('HTTP_PROXY')


# LZH: ChatGPT 对话类：作为微信机器人的兜底回复，把用户文本交给大模型生成回答。
class ChatGPT:

    # LZH: 方法说明：调用 OpenAI ChatCompletion 接口生成回复。
    # LZH: 参数：prompt — 用户输入的文本；返回：str，模型回复内容或错误提示 "服务器出错了"；
    # LZH: 异常：内部捕获所有异常并记录日志，不向调用方抛出。
    @staticmethod
    def chat(prompt):
        try:
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                      messages=[{"role": "user", "content": prompt}])
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(e)
            return "服务器出错了"


# LZH: 命令处理类：启动时从数据库加载命令配置，负责命令查找、执行与帮助文本生成。
class CommandHandler:
    # LZH: 方法说明：初始化时一次性取出全部命令配置，供后续查找复用。
    # LZH: 参数：无；返回：None；异常：数据库异常向上抛出。
    def __init__(self):
        self.commands = commands.objects.all()

    # LZH: 方法说明：按标题（忽略大小写）查找命令并执行。
    # LZH: 参数：title — 命令标题；返回：str，命令输出或未找到提示；
    # LZH: 异常：无，执行阶段的异常在 __run_command__ 内捕获。
    def run(self, title):
        """
        运行命令
        :param title: 命令
        :return: 返回命令执行结果
        """
        # LZH: 在内存中做忽略大小写的标题匹配，取第一条命中的命令配置。
        cmd = list(
            filter(
                lambda x: x.title.upper() == title.upper(),
                self.commands))
        if cmd:
            return self.__run_command__(cmd[0].command)
        else:
            return "未找到相关命令，请输入hepme获得帮助。"

    # LZH: 方法说明：以子进程方式执行命令字符串，并返回标准输出。
    # LZH: 参数：cmd — 要执行的命令字符串；返回：str，命令输出或出错提示 '命令执行出错!'；
    # LZH: 异常：捕获 BaseException 后转为提示文本返回。
    def __run_command__(self, cmd):
        try:
            # LZH: os.popen 以只读管道执行命令，read() 读取全部标准输出。
            res = os.popen(cmd).read()
            return res
        except BaseException:
            return '命令执行出错!'

    # LZH: 方法说明：拼装帮助文本，每行格式为“命令标题:命令描述”。
    # LZH: 参数：无；返回：str，多行帮助文本；异常：无。
    def get_help(self):
        rsp = ''
        for cmd in self.commands:
            rsp += '{c}:{d}\n'.format(c=cmd.title, d=cmd.describe)
        return rsp


# LZH: 本地调试入口：直接用 python 运行本文件时，对 ChatGPT 做一次冒烟测试。
if __name__ == '__main__':
    chatbot = ChatGPT()
    prompt = "写一篇1000字关于AI的论文"
    print(chatbot.chat(prompt))
