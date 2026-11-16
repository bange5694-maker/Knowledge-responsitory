# -*- coding: utf-8 -*-
"""第五周数据模型设计说明书的内容块。

同一份 BLOCKS 同时供 Markdown 与 docx 渲染，保证两种输出一致。
块类型：
  ("title", text) / ("center", text)
  ("h1", text) / ("h2", text)
  ("p", text) / ("note", text) / ("bullet", text)
  ("table", caption, headers, rows, widths_cm)
  ("figure", path, caption, height_cm, note)
  ("pagebreak",)
  ("section", "landscape" | "portrait")
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_data import (
    ENTITIES, ENTITY_ORDER, GROUP_INFO, GROUPS, GROUP_ORDER,
    FUNCTIONS, MATRIX, RELATIONSHIPS, CONSTRAINTS, CODE_SNAPSHOT,
)

BLOCKS = []


def add(*block):
    BLOCKS.append(block)


def table_rows(entity_key):
    return [[f[0], f[1], f[2], f[3], f[4]] for f in ENTITIES[entity_key]["fields"]]


# ---------------------------------------------------------------- 标题区
add("title", GROUP_INFO["title"])
add("center", "组号：" + GROUP_INFO["no"])
add("center", "小组成员：" + GROUP_INFO["members"])

# ---------------------------------------------------------------- 1 概述
add("h1", "1 软件系统概述")
add("p", "「知识分享」博客系统是在开源项目 DjangoBlog 基础上二次开发的知识分享平台。它要解决的问题可以概括为：让内容创作者能够发布、组织和维护文章，让读者能够浏览、检索和互动，让管理员能够配置站点并审计运行情况。系统在原有博客能力上补充了站内主题数据、界面定制、评论表情回应、AI 导读字段与站内问答等能力（站内问答的检索与页面实现目前在开发分支 D_branch，尚未合入 main）。")
add("p", "系统采用 Django 5.2 + MySQL 作为主数据存储；缓存默认使用 Django 本地内存（配置 DJANGO_REDIS_URL 后可切换 Redis）；全文检索默认使用 Whoosh，可通过环境变量切换 Elasticsearch；前端由 Vite + Tailwind CSS + Alpine.js 构建。业务代码分为 accounts（账户）、blog（内容）、comments（评论）、oauth（第三方登录）、servermanager（运维）五个应用，另有 djangoblog 公共配置与 AI 客户端。")
add("p", "从数据视角看，系统围绕五类数据组织：账户与权限（D1）、内容（D2）、评论（D3）、配置（D4）、日志（D5）。本文档分析这五类数据对应的 13 个业务 model、Django 会话辅助表和文章—标签中间表，给出 E-R 图、UML 类图、表结构、model 对应关系与主要约束。")
add("note", "建模依据：线上 main 分支 commit 81f2d69 的 models.py（与本地 D_branch 的数据模型一致）。Django 内置的 auth_group、auth_permission、django_admin_log、django_site 等框架表属于基础设施，不在正文展开；BlogUser 的 groups、user_permissions 两个多对多字段只在关系表中说明。字段类型按 MySQL 实际迁移类型标注。文中代码位置以 main 为准；D_branch 独有的 AI 问答实现会单独标注为“开发分支”。")

# ---------------------------------------------------------------- 2 功能与数据分析
add("h1", "2 功能与数据分析")
add("p", "按用户可见的主要功能归纳为 6 类。表 2-1 给出每类功能包含的子功能、处理的主要数据对象和对应代码；表 2-2 进一步给出数据对象与功能之间的读写关系。")

rows = [[str(f["no"]), f["name"], f["sub"], f["objects"], f["code"]] for f in FUNCTIONS]
add(
    "table", "表 2-1 主要功能与数据对象",
    ["序号", "主要功能", "包含的子功能", "主要数据对象", "对应代码"],
    rows, [0.9, 2.1, 4.2, 3.4, 4.0], 8.0,
)

add("h2", "2.1 主要功能说明")
add("p", "（1）内容浏览与检索。这是读者侧读多写少的路径：首页、分页、文章详情、分类、标签、作者页和时间归档直接读取 Article、Category、Tag、BlogUser；站内搜索通过 Whoosh 索引读取 Article 的标题和正文；友情链接读取 Links。该功能除文章浏览量自增外不修改业务表。")
add("p", "（2）账户与认证。注册写 BlogUser，并发送激活邮件、写 EmailSendLog；登录读写 Session；第三方登录读写 OAuthUser 与 OAuthConfig，未绑定用户先走补充邮箱流程；找回密码更新 BlogUser 的密码字段并写邮件日志。")
add("p", "（3）评论互动。发表评论/回复写 Comment，表情回应写 CommentReaction；展示评论时读 Article、BlogUser 和 BlogSettings（comment_need_review 控制审核）；审核动作更新 Comment.is_enable。Comment 通过 parent_comment_id 自关联保存回复层级，CommentReaction 通过联合唯一约束防止重复表情。")
add("p", "（4）内容与站点管理。后台对 13 个业务 model 做增删改查：文章管理写 Article 及其标签关联，分类/标签管理写 Category/Tag，站点设置写 BlogSettings，友链/侧边栏写 Links/SideBar，用户与第三方配置写 BlogUser/OAuthUser/OAuthConfig，评论管理写 Comment，运维配置写 commands/EmailSendLog。")
add("p", "（5）运维与通知。邮件发送写 EmailSendLog；后台命令维护写 commands；微信问答读取 commands、Article、Category，把文章卡片和分类列表返回给微信用户。该功能不新增业务表，主要复用内容与配置数据。")
add("p", "（6）AI 导读与站内问答。AI 导读把生成结果写回 Article 的 ai_summary、ai_highlights、ai_audience、ai_keywords、ai_status、ai_generated_at、ai_model 字段；站内问答读取 Article 的 AI 字段和 Comment 的索引内容，返回带引用的回答。该功能不新增表，AI 结果作为 Article 的扩展属性保存。需要说明的是：AI 字段与 djangoblog.ai.client 已随 main@81f2d69 合入；站内问答的检索、接口和页面实现目前只在开发分支 D_branch，尚未合入 main。")

matrix_headers = ["数据对象", "内容浏览", "账户认证", "评论互动", "内容管理", "运维通知", "AI 导读"]
matrix_rows = []
for key in ENTITY_ORDER:
    name = key if key != "ArticleTag" else "blog_article_tags"
    matrix_rows.append([name] + MATRIX.get(key, [""] * 6))
add(
    "table", "表 2-2 数据对象与主要功能的读写关系",
    matrix_headers, matrix_rows, [2.8, 1.95, 1.95, 1.95, 1.95, 1.95, 1.95],
)
add("note", "● 表示该功能会写入该数据对象，○ 表示只读，空白表示不涉及。矩阵按主要读写路径归纳，不排除个别辅助查询；Whoosh 索引是派生结构，未单列。")

# ---------------------------------------------------------------- 3 数据模型设计
add("h1", "3 数据模型设计")
add("p", "数据模型设计分三层表达：E-R 图回答“有哪些表、表之间是什么关系、重数多少”；UML 类图回答“代码里有哪些 model、关键属性是什么”；3.2 节的表结构给出每个字段的类型、主键、外键和约束。两张图都只画关键字段，完整字段以表结构为准，避免图面因字段过多而不可读。")
add("p", "E-R 图采用 Crow's Foot 记法：矩形为数据库表，框内列关键字段及类型；1 端画竖线，多端画分叉；虚线表示没有数据库外键的逻辑关联。类图采用 UML 类图记法：包对应数据域，类名为 model 类名，字段格式为“字段名（PK/FK/UK）”。")

add("h2", "3.1 实体关系与数据模型图")
add("p", "实体之间的主要关系汇总见表 3-1。重数按“左端 : 右端”书写；可选性说明外键是否允许为空；实现方式给出数据库外键、中间表或逻辑关联。")
rel_rows = []
for r in RELATIONSHIPS:
    rel_rows.append([
        r["name"],
        f'{r["a"]} — {r["b"]}',
        f'{r["card_a"]}:{r["card_b"]}',
        r["optional"],
        r["impl"],
        r["desc"],
    ])
rel_rows.append([
    "权限关联", "BlogUser — auth_group / auth_permission", "0..* : 0..*", "框架表",
    "M2M accounts_bloguser_groups / accounts_bloguser_user_permissions",
    "用户通过 Django 权限体系获得后台权限；属框架表，本文档不展开。",
])
add(
    "table", "表 3-1 实体关系说明",
    ["关系名", "参与实体", "重数", "可选性", "实现方式", "说明"],
    rel_rows, [1.4, 2.6, 1.7, 2.5, 3.8, 2.6], 8.0,
)
add("p", "在表 3-1 的关系基础上，图 3-1 用 Crow's Foot 记法给出数据库表及重数，图 3-2 用 UML 类图给出 model 类与关键属性。两张图均排在横向页上，图后回到纵向页继续表结构。")
add("h2", "3.1.1 关系设计说明")
add("p", "（1）结构关系。一对多关系由“多”端外键实现：BlogUser→Article/Comment/CommentReaction、Article→Comment、Comment→CommentReaction、Category→Article；多对多 Article↔Tag 由 blog_article_tags 中间表实现，并对 (article_id, tag_id) 联合唯一；Category.parent_category_id、Comment.parent_comment_id 为自关联，分别形成分类树和回复树。")
add("p", "（2）逻辑关系。BlogUser↔Session 通过 session_data 关联，OAuthConfig↔OAuthUser 通过 type 关联；两者没有数据库外键，重数与一致性由应用层保证。")
add("section", "landscape")
add("figure", os.path.join("imgs", "week5-er-diagram.png"), "图 3-1 数据模型 E-R 图", 16.2,
    "注：图中只列主键、外键、唯一键和关键业务字段；Article 与 Tag 的多对多通过中间表 blog_article_tags 显式表示。为避免连线交叉，OAuthConfig—OAuthUser 的按 type 逻辑关联、BlogUser—CommentReaction 的回应关系以及权限关联未在图中画出，完整关系见表 3-1。")
add("figure", os.path.join("imgs", "week5-class-diagram.png"), "图 3-2 数据模型 UML 类图", 16.2,
    "注：类图按五个数据域分包，只列关键属性；完整字段见 3.2 节表结构。与图 3-1 相同，OAuthConfig—OAuthUser、BlogUser—CommentReaction 和权限关联未在图中画出，完整关系见表 3-1。")
add("section", "portrait")

add("h2", "3.2 实体表结构")
add("p", "下列表结构按数据库实际列列出，包含继承字段：Article、Category、Tag 继承 BaseModel 的 id、creation_time、last_modify_time；BlogUser 继承 AbstractUser 的 password、last_login、is_superuser、username、first_name、last_name、email、is_staff、is_active、date_joined。")
add("p", "两个容易对错的地方：BlogUser 的实际表名是 accounts_bloguser（不是 auth_user）；Links、SideBar 的修改时间字段是 last_mod_time（不是 last_modify_time）。groups、user_permissions 属 Django 权限框架表，不列入 accounts_bloguser 的列，详见关系表 3-1 的“权限关联”行。")

# 3.2.1 D1
add("h2", "3.2.1 账户与权限数据（D1）")
for key, cap in [("BlogUser", "表 3-2 用户表 BlogUser（accounts_bloguser）"),
                 ("OAuthUser", "表 3-3 第三方账号表 OAuthUser（oauth_oauthuser）"),
                 ("OAuthConfig", "表 3-4 第三方登录配置表 OAuthConfig（oauth_oauthconfig）"),
                 ("Session", "表 3-5 会话表 Session（django_session）")]:
    add("table", cap, ["字段名", "中文名", "类型", "约束/取值", "说明"], table_rows(key),
        [3.4, 2.2, 2.0, 3.8, 3.2])
    for note in ENTITIES[key]["notes"]:
        add("note", f"（{' '.join(cap.split(' ')[:2])}）{note}")

# 3.2.2 D2
add("h2", "3.2.2 内容数据（D2）")
for key, cap in [("Article", "表 3-6 文章表 Article（blog_article）"),
                 ("Category", "表 3-7 分类表 Category（blog_category）"),
                 ("Tag", "表 3-8 标签表 Tag（blog_tag）"),
                 ("ArticleTag", "表 3-9 文章—标签关联表 blog_article_tags")]:
    add("table", cap, ["字段名", "中文名", "类型", "约束/取值", "说明"], table_rows(key),
        [3.4, 2.2, 2.0, 3.8, 3.2])
    for note in ENTITIES[key]["notes"]:
        add("note", f"（{' '.join(cap.split(' ')[:2])}）{note}")

# 3.2.3 D3
add("h2", "3.2.3 评论数据（D3）")
for key, cap in [("Comment", "表 3-10 评论表 Comment（comments_comment）"),
                 ("CommentReaction", "表 3-11 评论表情表 CommentReaction（comments_commentreaction）")]:
    add("table", cap, ["字段名", "中文名", "类型", "约束/取值", "说明"], table_rows(key),
        [3.4, 2.2, 2.0, 3.8, 3.2])
    for note in ENTITIES[key]["notes"]:
        add("note", f"（{' '.join(cap.split(' ')[:2])}）{note}")

# 3.2.4 D4
add("h2", "3.2.4 配置数据（D4）")
for key, cap in [("BlogSettings", "表 3-12 站点设置表 BlogSettings（blog_blogsettings）"),
                 ("Links", "表 3-13 友情链接表 Links（blog_links）"),
                 ("SideBar", "表 3-14 侧边栏表 SideBar（blog_sidebar）"),
                 ("commands", "表 3-15 后台命令表 commands（servermanager_commands）")]:
    add("table", cap, ["字段名", "中文名", "类型", "约束/取值", "说明"], table_rows(key),
        [3.4, 2.2, 2.0, 3.8, 3.2])
    for note in ENTITIES[key]["notes"]:
        add("note", f"（{' '.join(cap.split(' ')[:2])}）{note}")

# 3.2.5 D5
add("h2", "3.2.5 日志数据（D5）")
for key, cap in [("EmailSendLog", "表 3-16 邮件发送日志表 EmailSendLog（servermanager_emailsendlog）")]:
    add("table", cap, ["字段名", "中文名", "类型", "约束/取值", "说明"], table_rows(key),
        [3.4, 2.2, 2.0, 3.8, 3.2])
    for note in ENTITIES[key]["notes"]:
        add("note", f"（{' '.join(cap.split(' ')[:2])}）{note}")

# 3.3 对应关系
add("h2", "3.3 实体与代码 model 的对应关系")
add("p", "实体与 model 的对应关系见表 3-17，表中给出 model 类、应用、代码位置以及每个 model 的数据与职责。对应关系的基本原则是：一个业务 model 对应一张表；blog_article_tags 是 Django 为 Article.tags 自动生成的中间表，没有独立 model 类；Session 是 Django 内置 model，不在业务应用内。")
map_rows = []
for key in ENTITY_ORDER:
    e = ENTITIES[key]
    if key == "Session":
        model_cls, app, loc = "Session", "Django 内置", "django.contrib.\nsessions"
    elif key == "ArticleTag":
        model_cls, app, loc = "无（自动生成）", "blog", "Django M2M through"
    else:
        model_cls, app, loc = e["model"], e["app"], f"{e['app']}/models.py"
    map_rows.append([f'{e["cn"]}\n{e["table"]}', model_cls, app, loc, e["responsibility"]])
add(
    "table", "表 3-17 实体与代码 model 对应表",
    ["实体/表名", "model 类", "所在应用", "代码位置", "数据与职责"],
    map_rows, [2.8, 2.5, 2.3, 2.5, 4.5], 8.0,
)

# 3.4 约束
add("h2", "3.4 主要约束与业务规则")
add("p", "模型层和数据库层的主要约束见表 3-18。这些约束是数据库设计、后台校验和前端提示的共同依据。")
add(
    "table", "表 3-18 主要约束与业务规则",
    ["编号", "约束/规则", "依据"],
    [[c[0], c[1], c[2]] for c in CONSTRAINTS], [1.2, 7.8, 5.6], 8.0,
)

# 3.5 小结
add("h2", "3.5 数据模型特点小结")
add("bullet", "以内容为中心：Article 是核心实体，Category、Tag、Comment、CommentReaction 围绕文章组织；BlogUser 贯穿文章、评论和表情的所有权与互动关系；AI 导读字段直接扩展 Article，不新增表。")
add("bullet", "评论支持嵌套与审核：Comment.parent_comment 自关联实现无限层级回复；is_enable 与 BlogSettings.comment_need_review 两级控制显示/审核；CommentReaction 用联合唯一约束防止重复表情。")
add("bullet", "账户兼顾本地与第三方：BlogUser 承担本站认证；OAuthUser 记录第三方身份与绑定关系；OAuthConfig 管理平台参数；Session 保存登录状态。")
add("bullet", "配置与日志独立：BlogSettings、Links、SideBar、commands、EmailSendLog 不依赖内容表，便于后台维护和审计；BlogSettings 通过 clean() 保证单例。")


