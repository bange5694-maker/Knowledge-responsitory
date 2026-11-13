# 第 3 章素材 · servermanager（李子涵）

> 用途：报告第 3 章「人工分析代码的质量情况」中 servermanager 部分的素材，交给何君杰汇总。
> 范围：servermanager 11 个业务文件 146 行注释 + `tests.py` 12 行（不含 migrations）。
> 依据：`feat/app-servermanager`（提交 `bcde8aa`，PR #7），文中行号以该版本为准。
> 写法：按模板 3.1～3.4 组织；3.4 的 Q1～Q10 可直接在第 6 章改进计划里引用。

---

## 3.1 代码风格

**总体结论**：servermanager 基本符合 PEP 8——4 个空格缩进、函数与变量 snake_case、导入按「标准库 / 第三方 / 项目内」三组分开；但有两处明显偏差：一是 `blogapi.py` 用 `self.__max_takecount__` 这种双下划线包围的名字存普通常量，属于 dunder 命名误用；二是 `models.py` 的模型类名 `commands` 全小写，不符合团队规范 3.1 要求的 PascalCase（同文件另一个模型 `EmailSendLog` 是对的）。

**正面片段**（`servermanager/robot.py:5-18`，导入分组）：

```python
5   import logging
6   import os
7   import re
8
9   import jsonpickle
10  from django.conf import settings
11  from werobot import WeRoBot
12  from werobot.replies import ArticlesReply, Article
13  from werobot.session.filestorage import FileStorage
14
15  from djangoblog.utils import get_sha256
16  from servermanager.api.blogapi import BlogApi
17  from servermanager.api.commonapi import ChatGPT, CommandHandler
18  from .MemcacheStorage import MemcacheStorage
```

说明：三组导入之间各空一行，组内按模块名字母序排列，相对导入放最后，与团队规范 3.3 一致。

**偏差片段**（`servermanager/api/blogapi.py:13-18`）：

```python
13      def __init__(self):
14          self.searchqueryset = SearchQuerySet()
15          # LZH: 先做一次空查询，让检索对象完成与后端索引的绑定。
16          self.searchqueryset.auto_query('')
17          # LZH: 单次最多返回 8 条，控制微信图文卡片的数量。
18          self.__max_takecount__ = 8
```

说明：`__max_takecount__` 前后都是双下划线，Python 里这种写法是给解释器保留的 dunder 命名，用在实例常量上会让人误以为是特殊方法/属性，也起不到「私有」作用。建议改成模块级常量 `_MAX_TAKE_COUNT = 8`、实例属性用 `self.max_take_count`。同类问题还有 `servermanager/models.py:10` 的 `class commands`。

---

## 3.2 代码设计

**总体结论**：分层清楚——`robot.py` 只做「消息分发 + 会话状态机」，`api/blogapi.py` 收口所有检索与 ORM 查询，`api/commonapi.py` 收口对话与命令执行，`MemcacheStorage.py` 用适配器模式把 WeRoBot 的 `SessionStorage` 接到项目缓存；`views.py` 保持空文件、路由直接把 `make_view(robot)` 挂上，没有多余一层。主要不足在**执行层没有隔离**：命令字符串原样交给 `os.popen`，是整份代码里耦合最紧、风险最高的一处。

**片段 1**（`servermanager/robot.py:22-36`，存储选择与单例复用）：

```python
22  robot = WeRoBot(token=os.environ.get('DJANGO_WEROBOT_TOKEN')
23                        or 'lylinux', enable_session=True)
24  # LZH: 会话存储选择：先探测缓存是否可用，可用则把 session 存入缓存。
25  memstorage = MemcacheStorage()
26  if memstorage.is_available:
27      robot.config['SESSION_STORAGE'] = memstorage
28  else:
29      # LZH: 缓存不可用时的兜底方案：清理上次遗留的会话文件，改用本地文件存储。
30      if os.path.exists(os.path.join(settings.BASE_DIR, 'werobot_session')):
31          os.remove(os.path.join(settings.BASE_DIR, 'werobot_session'))
32      robot.config['SESSION_STORAGE'] = FileStorage(filename='werobot_session')
33
34  # LZH: 全局单例：博客查询接口与命令处理器，避免每条消息都重复构造。
35  blogapi = BlogApi()
36  cmd_handler = CommandHandler()
```

说明：`robot` 是单例，`SESSION_STORAGE` 的注入点收在一个模块里，上层处理器完全看不到存储实现——这是信息隐藏做得好的地方；`BlogApi`、`CommandHandler` 同样只在模块加载时构造一次，不会每条微信消息都新建对象。

**片段 2**（`servermanager/MemcacheStorage.py:11-29`，适配器模式）：

```python
11  class MemcacheStorage(SessionStorage):
12      # LZH: 方法说明：初始化缓存键前缀与缓存后端。
13      # LZH: 参数：prefix — 缓存键前缀，默认 'ws_'，用于隔离微信会话与其他业务缓存；返回：None。
14      def __init__(self, prefix='ws_'):
15          self.prefix = prefix
16          self.cache = cache
17
18      # LZH: 属性说明：探测缓存是否可用——写入 "1" 后立即读回并比对。
19      # LZH: 参数：无；返回：bool，True 表示缓存可用；异常：缓存后端异常向上抛出，由调用方兜底。
20      @property
21      def is_available(self):
22          value = "1"
23          self.set('checkavaliable', value=value)
24          return value == self.get('checkavaliable')
25
26      # LZH: 方法说明：为会话 key 拼接统一前缀，避免与其他业务缓存冲突。
27      # LZH: 参数：s — 原始 key（微信用户 openid）；返回：str，带前缀的缓存 key。
28      def key_name(self, s):
29          return '{prefix}{s}'.format(prefix=self.prefix, s=s)
```

说明：只实现 `get / set / delete / key_name` 四个约定方法就能替换 WeRoBot 的会话后端，`ws_` 前缀把微信会话和项目其他缓存隔开，内聚度高、对外零侵入。

**偏差片段**（`servermanager/api/commonapi.py:66-72`，执行层无隔离）：

```python
66      def __run_command__(self, cmd):
67          try:
68              # LZH: os.popen 以只读管道执行命令，read() 读取全部标准输出。
69              res = os.popen(cmd).read()
70              return res
71          except BaseException:
72              return '命令执行出错!'
```

说明：`cmd` 来自数据库字段（`servermanager/models.py:14`）并最终由管理员微信输入触发，整条链路没有任何白名单或转义，业务层直接和操作系统 shell 耦合在一起；`except BaseException` 又把 `KeyboardInterrupt`、`SystemExit` 一起吞掉，问题排查时连痕迹都留不下（详见 Q1）。

---

## 3.3 编程技能

**总体结论**：servermanager 里有几处能看出作者对框架和业务的理解：

1. **多轮会话状态机**：`MessageHandler.handler()` 用「进入管理模式 → 校验密码 → 暂存命令 → 回 Y 才执行」四段流转，把管理员操作做成微信里的多轮对话，并给密码失败加了 3 次上限；
2. **图文卡片自动组装**：`convert_to_article_reply()` 从文章正文用正则抠出第一张图片当缩略图、用 `truncatechars_content` 截断摘要，一次返回多张卡片；
3. 检索层用 `sqs.load_all()` 一次性把命中结果对应的数据库对象取回，避免逐条回表；
4. 会话状态用 `jsonpickle` 序列化进缓存，`WxUserInfo` 这类自定义对象不用手写 `to_dict`。

**片段 1**（`servermanager/robot.py:204-217`，密码失败限次 + 命令二次确认）：

```python
204             else:
205                 # LZH: 校验失败：累计失败次数，超过 3 次直接清空会话（防止暴力破解）。
206                 if self.userinfo.Count >= 3:
207                     self.userinfo = WxUserInfo()
208                     self.save_session()
209                     return "超过验证次数"
210                 self.userinfo.Count += 1
211                 self.save_session()
212                 return "验证失败，请重新输入管理员密码:"
213         # LZH: 分支四：管理员已通过校验 —— 进入命令执行阶段。
214         if self.userinfo.isAdmin and self.userinfo.isPasswordSet:
215             # LZH: 上一条命令已暂存且本次回复 Y，视为二次确认，立即执行该命令。
216             if self.userinfo.Command != '' and info.upper() == 'Y':
217                 return cmd_handler.run(self.userinfo.Command)
```

说明：失败计数存在会话里，超过 3 次直接换一个全新的 `WxUserInfo`，等于强制退出管理员模式；命令先暂存、回 `Y` 才执行，避免微信里误触就执行服务器命令——这是把「危险操作二次确认」真正落到了代码里。

**片段 2**（`servermanager/robot.py:43-60`，图文卡片组装）：

```python
43  def convert_to_article_reply(articles, message):
44      reply = ArticlesReply(message=message)
45      from blog.templatetags.blog_tags import truncatechars_content
46      for post in articles:
47          # LZH: 从文章正文中提取第一张图片（png/jpg）作为卡片缩略图，找不到则留空。
48          imgs = re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', post.body)
49          imgurl = ''
50          if imgs:
51              imgurl = imgs[0]
52          # LZH: 每条文章生成一张卡片：标题、摘要（截断正文）、缩略图、原文链接。
53          article = Article(
54              title=post.title,
55              description=truncatechars_content(post.body),
56              img=imgurl,
57              url=post.get_full_url()
58          )
59          reply.add_article(article)
60      return reply
```

说明：把「文章对象 → 微信卡片」的转换收在一个函数里，检索、分类、最新文章三个命令共用；缩略图缺失时留空而不是报错，微信端不会因为一篇文章没图就整条消息发不出去。

---

## 3.4 代码质量问题

| 编号 | 位置（文件:行） | 问题 | 严重程度 | 是否已修复 | 修复建议（供第 6 章用） |
|---|---|---|---|---|---|
| Q1 | `servermanager/api/commonapi.py:66-72` | 管理员命令原样交给 `os.popen(cmd).read()` 执行，命令内容来自数据库字段且无白名单/转义，等于把 shell 暴露在微信对话里；`except BaseException` 还会吞掉 `KeyboardInterrupt`、`SystemExit`，违反团队规范 3.5 | 高 | 否 | 命令改「白名单 + 参数列表」执行（`subprocess.run([...], shell=False)`），或只允许执行预注册的命令 ID；异常改捕 `subprocess.SubprocessError`/`OSError` 并记日志 |
| Q2 | `servermanager/api/commonapi.py:27-34` | `requirements.txt:21` 固定 `openai==2.54.0`，代码却用 0.x 的 `openai.ChatCompletion.create`；新版 SDK 只提供 `client.chat.completions`，该入口在 1.x 即被移除（访问会抛 `APIRemovedInV1`/`AttributeError`），异常被 `except Exception` 吞掉后固定返回「服务器出错了」，兜底聊天实际不可用 | 高 | 否 | 改用 `OpenAI().chat.completions.create(...)`（新版 SDK），并用 `logger.exception` 记录失败原因 |
| Q3 | `servermanager/robot.py:215-217` | 命令执行后没有清空 `userinfo.Command`，之后再发一个 `Y` 会重复执行上一条命令；`Command` 为空时输入 `Y` 又会被当成新命令暂存 | 中 | 否 | `run()` 之后 `self.userinfo.Command = ''` 并 `save_session()`；单独判断「无待执行命令」直接提示，而不是把 `Y` 存成命令 |
| Q4 | `servermanager/robot.py:197-199` | `settings.TESTING` 为真时把明文 `'123'` 赋给 `passwd`，紧接着却仍与 `get_sha256(get_sha256(input))` 比较，逻辑上永远不可能相等；`tests.py` 对该分支没有断言，问题被掩盖 | 中 | 否 | 测试态直接比较明文（如 `return info == '123'`），并把「验证成功后 isPasswordSet 为真」写进测试断言 |
| Q5 | `servermanager/api/blogapi.py:38-40` | `if articles:` 对 QuerySet 做真值判断会先执行整条查询（全表求值），再在内存里切前 8 条，等于每次「分类文章」都扫一遍表，而不是 `LIMIT 8` | 中 | 否 | 直接 `return articles[:8] or None`，或用 `articles.exists()` 判断后再切片 |
| Q6 | `servermanager/robot.py:25-32`、`servermanager/MemcacheStorage.py:20-24` | `is_available` 内部没有 `try/except`，缓存后端不可用时会直接抛异常，模块导入即失败，「降级到文件存储」的兜底分支根本走不到 | 中 | 否 | 在 `is_available` 里包 `try/except Exception: return False`，并 `logger.warning` 记录降级原因 |
| Q7 | `servermanager/api/commonapi.py:41-42`、`servermanager/robot.py:35-36` | `CommandHandler` 在模块导入时构造并缓存 `commands.objects.all()` 的求值结果，之后后台新增/修改命令不生效，必须重启进程；后台改配置的预期落空 | 中 | 否 | 改成每次 `run()` 时重新查询（或加缓存并在后台保存时失效），必要时用 `django.core.cache` 控制 TTL |
| Q8 | `servermanager/models.py:10`、`servermanager/api/blogapi.py:18` | 模型类名 `commands` 全小写，违反团队规范 3.1 的 PascalCase；`__max_takecount__` 双下划线包围属 dunder 命名误用 | 低 | 否 | 类名改 `Command`（需同步 admin/导入与迁移，本次不动迁移）；常量改 `_MAX_TAKE_COUNT` |
| Q9 | `servermanager/robot.py:37`、`servermanager/robot.py:155-158` | `logger` 定义后从未使用；`except Exception as e` 里 `e` 未使用也不打日志，会话反序列化失败被静默吞掉，线上只能看到「莫名其妙变成普通用户」 | 低 | 否 | 用 `logger.exception('会话反序列化失败 userid=%s', userid)` 替换静默分支，删掉未用的 `logger` 或补上日志 |
| Q10 | `servermanager/tests.py:4-5,24`、`servermanager/robot.py:45` | `tests.py` 里 `RequestFactory`、`timezone` 导入未使用；`test_validate_comment` 连续调用 `handler()` 但几乎不断言结果，只验证「不报错」；`robot.py` 在函数内部导入 `blog_tags`，违反团队规范 3.3 | 低 | 否 | 删除未用导入、给关键分支补断言（验证通过/失败/超过次数）；局部导入若为规避循环依赖，写明注释，否则提到文件头 |

> 说明：以上问题均为本次人工阅读发现，全部未修复（本次作业只加注释，不改业务逻辑）；修复建议可直接用于报告第 6 章「下一步的改进计划」。
