# -*- coding: utf-8 -*-
"""第五周数据模型说明书的单一事实源。

实体、字段、关系、功能与约束都写在这里；E-R 图、UML 类图、Markdown 与 docx
均由本文件生成，避免图、表、文字三处口径不一致。

字段类型按 Django 5.2 + MySQL 的实际迁移结果标注：
AutoField -> int，BigAutoField -> bigint，CharField/SlugField -> varchar，
TextField -> longtext，DateTimeField -> datetime(6)，BooleanField -> tinyint(1)，
PositiveIntegerField -> int unsigned，JSONField -> json。
"""

GROUP_ORDER = ["D1", "D2", "D3", "D4", "D5"]

GROUPS = {
    "D1": "账户与权限数据",
    "D2": "内容数据",
    "D3": "评论数据",
    "D4": "配置数据",
    "D5": "日志数据",
}

ENTITIES = {
    "BlogUser": {
        "cn": "用户",
        "app": "accounts",
        "model": "BlogUser",
        "table": "accounts_bloguser",
        "group": "D1",
        "diagram": True,
        "responsibility": (
            "本站用户账号。继承 Django 的 AbstractUser，复用用户名、密码、邮箱、"
            "后台权限等认证字段，并扩展昵称、来源和创建/修改时间；承担登录认证、"
            "后台权限、文章作者、评论作者和表情回应者的身份锚点。"
        ),
        "fields": [
            ("id", "用户编号", "bigint", "PK，自增", "主键"),
            ("password", "密码", "varchar(128)", "非空", "Django 密码哈希，不存明文"),
            ("last_login", "最后登录时间", "datetime(6)", "可空", "最近一次登录时间"),
            ("is_superuser", "超级用户", "tinyint(1)", "非空，默认 0", "拥有全部权限标记"),
            ("username", "用户名", "varchar(150)", "UK，非空", "登录名，全局唯一"),
            ("first_name", "名", "varchar(150)", "可空", "AbstractUser 标准字段"),
            ("last_name", "姓", "varchar(150)", "可空", "AbstractUser 标准字段"),
            ("email", "邮箱", "varchar(254)", "可空", "激活邮件、评论通知的收件地址"),
            ("is_staff", "后台权限", "tinyint(1)", "非空，默认 0", "是否允许进入 admin 后台"),
            ("is_active", "是否激活", "tinyint(1)", "非空，默认 1", "邮箱验证前由注册视图置 0"),
            ("date_joined", "注册时间", "datetime(6)", "非空", "AbstractUser 标准字段"),
            ("nickname", "昵称", "varchar(100)", "可空", "前台作者信息展示名"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "业务扩展字段"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "业务扩展字段"),
            ("source", "注册来源", "varchar(100)", "可空", "Register、adminsite 等渠道标识"),
        ],
        "notes": [],

        "key_fields": [
            "id (PK)",
            "username (UK)",
            "password",
            "email",
            "is_staff",
            "is_active",
            "nickname",
            "source",
        ],
    },
    "OAuthUser": {
        "cn": "第三方账号",
        "app": "oauth",
        "model": "OAuthUser",
        "table": "oauth_oauthuser",
        "group": "D1",
        "diagram": True,
        "responsibility": (
            "第三方平台账号与本站用户的绑定记录。保存 openid、昵称、token、头像、"
            "平台类型、邮箱和原始 metadata；author 为空表示尚未绑定本站用户，"
            "配合“补充邮箱”流程完成绑定。"
        ),
        "fields": [
            ("id", "编号", "bigint", "PK，自增", "主键"),
            ("author_id", "绑定用户", "bigint", "FK→accounts_bloguser.id，可空", "为空表示尚未绑定"),
            ("openid", "第三方标识", "varchar(50)", "非空", "平台返回的用户 ID"),
            ("nickname", "第三方昵称", "varchar(50)", "非空", "平台昵称"),
            ("token", "访问令牌", "varchar(150)", "可空", "第三方 access token"),
            ("picture", "头像地址", "varchar(350)", "可空", "第三方头像 URL"),
            ("type", "平台类型", "varchar(50)", "非空", "github、weibo、qq 等"),
            ("email", "第三方邮箱", "varchar(50)", "可空", "可能缺失，需走补充邮箱流程"),
            ("metadata", "原始信息", "longtext", "可空", "平台返回的扩展 JSON/文本"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "首次授权时间"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "最近同步时间"),
        ],
        "notes": [],
        "key_fields": ["id (PK)", "author_id (FK)", "openid", "type", "email"],
    },
    "OAuthConfig": {
        "cn": "第三方登录配置",
        "app": "oauth",
        "model": "OAuthConfig",
        "table": "oauth_oauthconfig",
        "group": "D1",
        "diagram": True,
        "responsibility": (
            "每个第三方登录平台一条配置，保存 AppKey、AppSecret、回调地址和启用状态；"
            "登录页据此决定显示哪些第三方入口，clean() 保证同一 type 只有一条配置。"
        ),
        "fields": [
            ("id", "编号", "bigint", "PK，自增", "主键"),
            ("type", "平台类型", "varchar(10)", "非空，默认 'a'（历史遗留）；\n取值 weibo/google/\ngithub/facebook/qq", "平台标识；clean() 保证唯一"),
            ("appkey", "AppKey", "varchar(200)", "非空", "平台分配的应用 Key"),
            ("appsecret", "AppSecret", "varchar(200)", "非空", "平台分配的应用密钥"),
            ("callback_url", "回调地址", "varchar(200)", "非空，默认空串", "OAuth 授权回调 URL"),
            ("is_enable", "是否启用", "tinyint(1)", "非空，默认 1", "关闭后登录页不显示该入口"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "配置创建时间"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "配置修改时间"),
        ],
        "notes": [],
        "key_fields": ["id (PK)", "type (UK)", "appkey", "is_enable"],
    },
    "Session": {
        "cn": "会话",
        "app": "sessions",
        "model": "Session",
        "table": "django_session",
        "group": "D1",
        "diagram": True,
        "responsibility": (
            "Django 内置会话表，保存 session_key、session_data 和过期时间；"
            "登录状态、CSRF 与“记住我”有效期都落在这张表里，通过 session_data "
            "中的用户标识与 BlogUser 形成逻辑关联。"
        ),
        "fields": [
            ("session_key", "会话键", "varchar(40)", "PK", "浏览器 Cookie 中保存的会话标识"),
            ("session_data", "会话数据", "longtext", "非空", "编码后的会话内容，含用户标识"),
            ("expire_date", "过期时间", "datetime(6)", "非空", "会话失效时间"),
        ],
        "notes": ["Django 内置表，不是业务 model；本文档将其作为登录会话的辅助实体列出。"],
        "key_fields": ["session_key (PK)", "expire_date"],
    },
    "Article": {
        "cn": "文章",
        "app": "blog",
        "model": "Article",
        "table": "blog_article",
        "group": "D2",
        "diagram": True,
        "responsibility": (
            "博客核心内容实体。保存标题、Markdown 正文、发布时间、草稿/发布状态、"
            "评论开关、文章/页面类型、浏览量、作者、分类、排序、目录开关，以及 AI 导读"
            "所需的摘要、要点、受众、关键词、生成状态、生成时间和模型名；承担内容发布、"
            "详情展示、检索与 AI 导读的数据基础。"
        ),
        "fields": [
            ("id", "文章编号", "int", "PK，自增", "主键"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "继承自 BaseModel"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "继承自 BaseModel"),
            ("title", "标题", "varchar(200)", "UK，非空", "文章标题，全局唯一"),
            ("body", "正文", "longtext", "非空", "Markdown 源文"),
            ("pub_time", "发布时间", "datetime(6)", "非空", "默认当前时间"),
            ("status", "状态", "varchar(1)", "非空，默认 'p'", "d=草稿，p=已发布"),
            ("comment_status", "评论开关", "varchar(1)", "非空，默认 'o'", "o=开放，c=关闭"),
            ("type", "内容类型", "varchar(1)", "非空，默认 'a'", "a=文章，p=独立页面"),
            ("views", "浏览量", "int unsigned", "非空，默认 0", "阅读计数"),
            ("author_id", "作者", "bigint", "FK→accounts_bloguser.id，非空", "文章作者"),
            ("article_order", "排序", "int", "非空，默认 0", "置顶/排序值，越大越靠前"),
            ("show_toc", "显示目录", "tinyint(1)", "非空，默认 0", "详情页是否显示目录"),
            ("category_id", "分类", "int", "FK→blog_category.id，非空", "每篇文章必须属于一个分类"),
            ("ai_summary", "AI 摘要", "longtext", "非空，默认空串", "AI 生成的文章导读摘要"),
            ("ai_highlights", "AI 要点", "json", "非空，默认 []", "AI 提取的要点数组"),
            ("ai_audience", "AI 受众", "longtext", "非空，默认空串", "AI 判断的目标读者"),
            ("ai_keywords", "AI 关键词", "json", "非空，默认 []", "AI 提取的关键词数组"),
            ("ai_status", "AI 状态", "varchar(10)", "非空，默认 'pending'", "pending/done/failed/stale"),
            ("ai_generated_at", "AI 生成时间", "datetime(6)", "可空", "最近一次生成成功的时间"),
            ("ai_model", "AI 模型名", "varchar(50)", "非空，默认空串", "生成时使用的模型标识"),
        ],
        "notes": [
            "tags 为多对多字段，经 blog_article_tags 关联 blog_tag；不是 blog_article 的列。"
        ],
        "key_fields": [
            "id (PK)",
            "title (UK)",
            "author_id (FK)",
            "category_id (FK)",
            "status",
            "type",
            "pub_time",
            "views",
            "ai_status",
        ],
    },
    "Category": {
        "cn": "分类",
        "app": "blog",
        "model": "Category",
        "table": "blog_category",
        "group": "D2",
        "diagram": True,
        "responsibility": (
            "文章分类。保存分类名、父分类、URL 别名和排序值；parent_category 自关联"
            "支持多级分类树，承担文章归类与分类导航。"
        ),
        "fields": [
            ("id", "分类编号", "int", "PK，自增", "主键"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "继承自 BaseModel"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "继承自 BaseModel"),
            ("name", "分类名", "varchar(30)", "UK，非空", "分类名称，全局唯一"),
            ("parent_category_id", "父分类", "int", "FK→blog_category.id，可空", "为空表示顶级分类"),
            ("slug", "URL 别名", "varchar(60)", "非空，默认 'no-slug'", "save() 时按名称自动生成"),
            ("index", "排序", "int", "非空，默认 0", "分类展示顺序"),
        ],
        "notes": [],
        "key_fields": ["id (PK)", "name (UK)", "parent_category_id (FK)", "slug"],
    },
    "Tag": {
        "cn": "标签",
        "app": "blog",
        "model": "Tag",
        "table": "blog_tag",
        "group": "D2",
        "diagram": True,
        "responsibility": (
            "文章标签。保存标签名和 URL 别名，与 Article 多对多；承担主题标注、"
            "标签云和按标签浏览。"
        ),
        "fields": [
            ("id", "标签编号", "int", "PK，自增", "主键"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "继承自 BaseModel"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "继承自 BaseModel"),
            ("name", "标签名", "varchar(30)", "UK，非空", "标签名称，全局唯一"),
            ("slug", "URL 别名", "varchar(60)", "非空，默认 'no-slug'", "save() 时按名称自动生成"),
        ],
        "notes": ["article 是 Article.tags 的反向多对多关系，不是 blog_tag 的列。"],
        "key_fields": ["id (PK)", "name (UK)", "slug"],
    },
    "ArticleTag": {
        "cn": "文章-标签关联表",
        "app": "blog",
        "model": None,
        "table": "blog_article_tags",
        "group": "D2",
        "diagram": False,
        "responsibility": (
            "Article.tags 多对多关系的中间表，由 Django 自动创建；保存文章与标签的"
            "关联，联合唯一约束防止同一文章重复关联同一标签。"
        ),
        "fields": [
            ("id", "关联编号", "bigint", "PK，自增", "主键"),
            ("article_id", "文章", "int", "FK→blog_article.id，非空", "关联文章"),
            ("tag_id", "标签", "int", "FK→blog_tag.id，非空", "关联标签；与 article_id 联合唯一"),
        ],
        "notes": [],
        "key_fields": ["id (PK)", "article_id (FK)", "tag_id (FK)"],
    },
    "Comment": {
        "cn": "评论",
        "app": "comments",
        "model": "Comment",
        "table": "comments_comment",
        "group": "D3",
        "diagram": True,
        "responsibility": (
            "文章评论与回复。保存正文、作者、所属文章、父评论和审核/显示开关；"
            "parent_comment 自关联支持无限层级回复，is_enable 与站点审核开关共同"
            "决定评论是否展示。"
        ),
        "fields": [
            ("id", "评论编号", "bigint", "PK，自增", "主键"),
            ("body", "正文", "longtext", "非空", "评论内容，应用层限制 300 字"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "评论提交时间"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "评论修改时间"),
            ("author_id", "作者", "bigint", "FK→accounts_bloguser.id，非空", "评论者"),
            ("article_id", "所属文章", "int", "FK→blog_article.id，非空", "评论所属文章"),
            ("parent_comment_id", "父评论", "bigint", "FK→comments_comment.id，可空", "为空表示顶级评论"),
            ("is_enable", "是否显示", "tinyint(1)", "非空，默认 0", "审核/显示开关"),
        ],
        "notes": [
            "组合索引：idx_art_parent_enable(article_id, parent_comment_id, is_enable)；"
            "idx_enable_id(is_enable, -id)。"
        ],
        "key_fields": [
            "id (PK)",
            "article_id (FK)",
            "author_id (FK)",
            "parent_comment_id (FK)",
            "is_enable",
        ],
    },
    "CommentReaction": {
        "cn": "评论表情回应",
        "app": "comments",
        "model": "CommentReaction",
        "table": "comments_commentreaction",
        "group": "D3",
        "diagram": True,
        "responsibility": (
            "记录用户对评论的 Emoji 回应。保存评论、用户、表情类型和创建时间；"
            "联合唯一约束保证同一用户对同一评论的同种表情只能记一次，承担表情统计与展示。"
        ),
        "fields": [
            ("id", "回应编号", "bigint", "PK，自增", "主键"),
            ("comment_id", "评论", "bigint", "FK→comments_comment.id，非空", "被回应的评论"),
            ("user_id", "用户", "bigint", "FK→accounts_bloguser.id，非空", "回应者"),
            ("reaction_type", "表情类型", "varchar(10)", "非空", "8 种 Emoji 之一"),
            ("created_at", "回应时间", "datetime(6)", "非空", "auto_now_add"),
        ],
        "notes": ["联合唯一约束 (comment_id, user_id, reaction_type)。"],
        "key_fields": ["id (PK)", "comment_id (FK)", "user_id (FK)", "reaction_type"],
    },
    "BlogSettings": {
        "cn": "站点设置",
        "app": "blog",
        "model": "BlogSettings",
        "table": "blog_blogsettings",
        "group": "D4",
        "diagram": True,
        "responsibility": (
            "全站参数的单例配置。保存站点名称/描述/SEO/关键词、摘要长度、侧边栏与"
            "评论数量、AdSense、全站评论开关、主题配色、公共头尾、备案号、统计代码"
            "和评论审核总开关；clean() 保证全站只有一条记录。"
        ),
        "fields": [
            ("id", "配置编号", "bigint", "PK，自增", "主键"),
            ("site_name", "站点名称", "varchar(200)", "非空，默认空串", "站点标题"),
            ("site_description", "站点描述", "longtext", "非空，默认空串", "站点简介"),
            ("site_seo_description", "SEO 描述", "longtext", "非空，默认空串", "搜索引擎描述"),
            ("site_keywords", "SEO 关键词", "longtext", "非空，默认空串", "搜索引擎关键词"),
            ("article_sub_length", "摘要长度", "int", "非空，默认 300", "列表页摘要截取长度"),
            ("sidebar_article_count", "侧边栏文章数", "int", "非空，默认 10", "侧边栏最新/热门文章数量"),
            ("sidebar_comment_count", "侧边栏评论数", "int", "非空，默认 5", "侧边栏最新评论数量"),
            ("article_comment_count", "文章评论数", "int", "非空，默认 5", "详情页评论每页数量"),
            ("show_google_adsense", "显示 AdSense", "tinyint(1)", "非空，默认 0", "是否展示 Google 广告"),
            ("google_adsense_codes", "AdSense 代码", "longtext", "可空，默认空串", "广告代码片段"),
            ("open_site_comment", "全站评论开关", "tinyint(1)", "非空，默认 1", "关闭后全站不可评论"),
            ("color_scheme", "主题配色", "varchar(20)", "非空，默认 'purple'", "8 种主题配色之一"),
            ("global_header", "公共头部", "longtext", "可空，默认空串", "全站公共 head 片段"),
            ("global_footer", "公共尾部", "longtext", "可空，默认空串", "全站公共 footer 片段"),
            ("beian_code", "备案号", "varchar(2000)", "可空，默认空串", "ICP 备案号"),
            ("analytics_code", "统计代码", "longtext", "非空，默认空串", "网站统计脚本"),
            ("show_gongan_code", "显示公安备案", "tinyint(1)", "非空，默认 0", "是否展示公安备案号"),
            ("gongan_beiancode", "公安备案号", "longtext", "可空，默认空串", "公安备案文本"),
            ("comment_need_review", "评论需审核", "tinyint(1)", "非空，默认 0", "评论审核总开关"),
        ],
        "notes": ["单例约束由 BlogSettings.clean() 保证，不是数据库唯一索引。"],
        "key_fields": ["id (PK)", "site_name", "color_scheme", "comment_need_review"],
    },
    "Links": {
        "cn": "友情链接",
        "app": "blog",
        "model": "Links",
        "table": "blog_links",
        "group": "D4",
        "diagram": True,
        "responsibility": (
            "友情链接配置。保存名称、URL、排序、启用状态和展示位置；"
            "承担首页/列表页/文章页/轮播等位置的友链展示。"
        ),
        "fields": [
            ("id", "链接编号", "bigint", "PK，自增", "主键"),
            ("name", "名称", "varchar(30)", "UK，非空", "友链名称，全局唯一"),
            ("link", "链接地址", "varchar(200)", "非空", "URLField 存储的地址"),
            ("sequence", "排序", "int", "UK，非空", "展示顺序，唯一"),
            ("is_enable", "是否启用", "tinyint(1)", "非空，默认 1", "关闭后不展示"),
            ("show_type", "展示位置", "varchar(1)", "非空，默认 'i'", "i=首页，l=列表页，p=文章页，a=全部，s=轮播"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "创建时间"),
            ("last_mod_time", "修改时间", "datetime(6)", "非空", "最近修改时间（注意字段名无 ify）"),
        ],
        "notes": ["字段名是 last_mod_time，不是 last_modify_time，与 BaseModel 不同。"],
        "key_fields": ["id (PK)", "name (UK)", "link", "sequence", "show_type"],
    },
    "SideBar": {
        "cn": "侧边栏",
        "app": "blog",
        "model": "SideBar",
        "table": "blog_sidebar",
        "group": "D4",
        "diagram": True,
        "responsibility": (
            "可配置侧边栏。保存名称、HTML 内容、排序和启用状态；"
            "后台维护后按 sequence 顺序渲染到页面侧边栏。"
        ),
        "fields": [
            ("id", "侧边栏编号", "bigint", "PK，自增", "主键"),
            ("name", "名称", "varchar(100)", "非空", "侧边栏标题"),
            ("content", "内容", "longtext", "非空", "HTML 片段"),
            ("sequence", "排序", "int", "UK，非空", "展示顺序，唯一"),
            ("is_enable", "是否启用", "tinyint(1)", "非空，默认 1", "关闭后不渲染"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "创建时间"),
            ("last_mod_time", "修改时间", "datetime(6)", "非空", "最近修改时间（字段名无 ify）"),
        ],
        "notes": ["字段名是 last_mod_time，不是 last_modify_time。"],
        "key_fields": ["id (PK)", "name", "sequence", "is_enable"],
    },
    "commands": {
        "cn": "后台命令",
        "app": "servermanager",
        "model": "commands",
        "table": "servermanager_commands",
        "group": "D4",
        "diagram": True,
        "responsibility": (
            "微信机器人可执行命令的配置。保存命令标题、命令内容和描述；"
            "后台维护后供微信端 helpme 等命令查询执行。"
        ),
        "fields": [
            ("id", "命令编号", "bigint", "PK，自增", "主键"),
            ("title", "命令标题", "varchar(300)", "非空", "命令展示名"),
            ("command", "命令内容", "varchar(2000)", "非空", "实际执行的命令文本"),
            ("describe", "命令描述", "varchar(300)", "非空", "帮助信息中的用途说明"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "auto_now_add"),
            ("last_modify_time", "修改时间", "datetime(6)", "非空", "auto_now"),
        ],
        "notes": [],
        "key_fields": ["id (PK)", "title", "command"],
    },
    "EmailSendLog": {
        "cn": "邮件发送日志",
        "app": "servermanager",
        "model": "EmailSendLog",
        "table": "servermanager_emailsendlog",
        "group": "D5",
        "diagram": True,
        "responsibility": (
            "邮件发送审计。保存收件人、标题、正文、发送结果和创建时间；"
            "用于激活邮件、评论通知等场景的排错与审计。"
        ),
        "fields": [
            ("id", "日志编号", "bigint", "PK，自增", "主键"),
            ("emailto", "收件人", "varchar(300)", "非空", "收件邮箱地址"),
            ("title", "邮件标题", "varchar(2000)", "非空", "邮件主题"),
            ("content", "邮件内容", "longtext", "非空", "邮件正文"),
            ("send_result", "发送结果", "tinyint(1)", "非空，默认 0", "1=成功，0=失败/未发送"),
            ("creation_time", "创建时间", "datetime(6)", "非空", "auto_now_add"),
        ],
        "notes": [],
        "key_fields": ["id (PK)", "emailto", "send_result"],
    },
}

# 图与表中使用的实体顺序（按数据域）
ENTITY_ORDER = [
    "BlogUser", "OAuthUser", "OAuthConfig", "Session",
    "Article", "Category", "Tag", "ArticleTag",
    "Comment", "CommentReaction",
    "BlogSettings", "Links", "SideBar", "commands",
    "EmailSendLog",
]

RELATIONSHIPS = [
    {
        "name": "绑定",
        "a": "BlogUser", "b": "OAuthUser",
        "card_a": "1", "card_b": "0..*",
        "optional": "OAuthUser.author 可空",
        "impl": "FK oauth_oauthuser.author_id",
        "desc": "一个本站用户可绑定多个第三方账号；author 为空表示尚未绑定。",
    },
    {
        "name": "使用配置",
        "a": "OAuthConfig", "b": "OAuthUser",
        "card_a": "1", "card_b": "0..*",
        "optional": "按 type 逻辑关联，无外键",
        "impl": "OAuthUser.type = OAuthConfig.type",
        "desc": "每个第三方平台一条配置；OAuthUser 按 type 使用对应配置，属逻辑关联。",
    },
    {
        "name": "登录会话",
        "a": "BlogUser", "b": "Session",
        "card_a": "1", "card_b": "0..*",
        "optional": "逻辑关联",
        "impl": "session_data 中保存用户标识",
        "desc": "一个用户可有多个登录会话，支持多端登录；“记住我”延长 expire_date。",
    },
    {
        "name": "撰写",
        "a": "BlogUser", "b": "Article",
        "card_a": "1", "card_b": "0..*",
        "optional": "Article.author_id 非空",
        "impl": "FK blog_article.author_id",
        "desc": "一个用户可写多篇文章，每篇文章必有一个作者。",
    },
    {
        "name": "归属",
        "a": "Category", "b": "Article",
        "card_a": "1", "card_b": "0..*",
        "optional": "Article.category_id 非空",
        "impl": "FK blog_article.category_id",
        "desc": "一个分类可有多篇文章，每篇文章必须属于一个分类。",
    },
    {
        "name": "父子分类",
        "a": "Category", "b": "Category",
        "card_a": "1", "card_b": "0..*",
        "optional": "parent_category_id 可空",
        "impl": "FK blog_category.parent_category_id（自关联）",
        "desc": "父分类可挂多个子分类；为空表示顶级分类，支持多级分类树。",
    },
    {
        "name": "标注",
        "a": "Article", "b": "Tag",
        "card_a": "0..*", "card_b": "0..*",
        "optional": "标签可为空",
        "impl": "M2M blog_article_tags(article_id, tag_id)",
        "desc": "一篇文章多个标签，一个标签多篇文章；中间表联合唯一防重复。",
    },
    {
        "name": "发表",
        "a": "BlogUser", "b": "Comment",
        "card_a": "1", "card_b": "0..*",
        "optional": "Comment.author_id 非空",
        "impl": "FK comments_comment.author_id",
        "desc": "一个用户可发表多条评论，每条评论必有一个作者。",
    },
    {
        "name": "所属文章",
        "a": "Article", "b": "Comment",
        "card_a": "1", "card_b": "0..*",
        "optional": "Comment.article_id 非空",
        "impl": "FK comments_comment.article_id",
        "desc": "一篇文章可有多条评论，每条评论必须属于一篇文章。",
    },
    {
        "name": "父评论",
        "a": "Comment", "b": "Comment",
        "card_a": "1", "card_b": "0..*",
        "optional": "parent_comment_id 可空",
        "impl": "FK comments_comment.parent_comment_id（自关联）",
        "desc": "为空是顶级评论，非空是对某条评论的回复；支持无限层级嵌套。",
    },
    {
        "name": "针对",
        "a": "Comment", "b": "CommentReaction",
        "card_a": "1", "card_b": "0..*",
        "optional": "CommentReaction.comment_id 非空",
        "impl": "FK comments_commentreaction.comment_id",
        "desc": "一条评论可有多种表情回应。",
    },
    {
        "name": "回应",
        "a": "BlogUser", "b": "CommentReaction",
        "card_a": "1", "card_b": "0..*",
        "optional": "CommentReaction.user_id 非空",
        "impl": "FK comments_commentreaction.user_id",
        "desc": "一个用户可对多条评论回应；同用户同评论同表情唯一。",
    },
]

FUNCTIONS = [
    {
        "no": 1,
        "name": "内容浏览与检索",
        "sub": "首页文章列表、分页、文章详情、按分类浏览、按标签浏览、按作者浏览、时间归档、站内搜索、友情链接",
        "objects": "Article、Category、Tag、BlogUser、Links；搜索索引（Whoosh，派生结构）",
        "code": "blog.views、djangoblog/urls.py（search）",
    },
    {
        "no": 2,
        "name": "账户与认证",
        "sub": "注册、登录、退出登录、找回密码、第三方登录、补充邮箱",
        "objects": "BlogUser、OAuthUser、OAuthConfig、Session、EmailSendLog",
        "code": "accounts.views、oauth.views",
    },
    {
        "no": 3,
        "name": "评论互动",
        "sub": "发表评论、回复评论、评论表情回应、评论审核与显示",
        "objects": "Comment、CommentReaction、Article、BlogUser、BlogSettings",
        "code": "comments.views、comments.forms",
    },
    {
        "no": 4,
        "name": "内容与站点管理",
        "sub": "文章管理、分类/标签管理、友链/侧边栏管理、站点设置、评论管理、用户管理、第三方账号与配置管理",
        "objects": "全部 13 个业务 model",
        "code": "各应用 admin.py、djangoblog.admin_site",
    },
    {
        "no": 5,
        "name": "运维与通知",
        "sub": "邮件发送与日志、后台命令维护、微信问答",
        "objects": "EmailSendLog、commands、Article、Category",
        "code": "servermanager.models、servermanager.robot",
    },
    {
        "no": 6,
        "name": "AI 导读与站内问答",
        "sub": "文章 AI 摘要/要点/受众/关键词生成与状态维护、站内问答检索与引用",
        "objects": "Article（AI 字段）、Comment（问答索引）、Whoosh 索引",
        "code": "djangoblog.ai.client（main）；站内问答在 D_branch",
    },
]

# 数据对象 × 主要功能矩阵：● 写，○ 读，空 不涉及
MATRIX_SYMBOLS = {"W": "●", "R": "○", "": ""}
MATRIX = {
    "Article": ["○", "", "○", "●", "○", "●"],
    "Category": ["○", "", "", "●", "○", ""],
    "Tag": ["○", "", "", "●", "", ""],
    "ArticleTag": ["○", "", "", "●", "", ""],
    "Comment": ["", "", "●", "●", "", "○"],
    "CommentReaction": ["", "", "●", "●", "", ""],
    "BlogUser": ["○", "●", "○", "●", "", ""],
    "OAuthUser": ["", "●", "", "●", "", ""],
    "OAuthConfig": ["", "○", "", "●", "", ""],
    "Session": ["○", "●", "", "", "", ""],
    "BlogSettings": ["", "○", "○", "●", "", ""],
    "Links": ["○", "", "", "●", "", ""],
    "SideBar": ["○", "", "", "●", "", ""],
    "commands": ["", "", "", "●", "●", ""],
    "EmailSendLog": ["", "●", "", "○", "●", ""],
}

CONSTRAINTS = [
    ("C1", "文章标题唯一，且每篇文章必须指定分类。", "Article.title unique；category_id 非空"),
    ("C2", "文章状态 d/p、内容类型 a/p、评论开关 o/c；AI 状态 pending/done/failed/stale。", "Article 的 choices 定义"),
    ("C3", "评论正文非空且不超过 300 字；is_enable 默认 False；是否需审核由 BlogSettings.comment_need_review 决定。", "Comment.body、is_enable；BlogSettings"),
    ("C4", "同一用户对同一评论的同种表情只能记录一次。", "CommentReaction.unique_together"),
    ("C5", "用户名全局唯一；注册后邮箱验证前 is_active 为 False。", "BlogUser.username；RegisterView/ActivateView"),
    ("C6", "第三方账号可暂不绑定本站用户；每个平台只能有一条 OAuth 配置。", "OAuthUser.author 可空；OAuthConfig.clean()"),
    ("C7", "站点配置全站只能有一条记录。", "BlogSettings.clean()"),
    ("C8", "友链名称与排序唯一；侧边栏排序唯一。", "Links.name/sequence unique；SideBar.sequence unique"),
    ("C9", "分类支持多级：父分类可为空，子分类通过 parent_category_id 自关联。", "Category.parent_category_id"),
    ("C10", "文章与标签的关联不允许重复。", "blog_article_tags 联合唯一 (article_id, tag_id)"),
    ("C11", "评论列表按 (article_id, parent_comment_id, is_enable) 建组合索引；侧边栏评论按 (is_enable, -id) 建索引。", "Comment.Meta.indexes"),
    ("C12", "用户通过 groups、user_permissions 接入 Django 权限体系。", "BlogUser 继承 AbstractUser"),
]

CODE_SNAPSHOT = "main@81f2d69（与本地 D_branch 的 models.py、migrations 一致）"

GROUP_INFO = {
    "no": "第 13 组",
    "members": "丁昊、席佳宁、朱宇豪、何君杰、李子涵",
    "title": "「知识分享」博客系统的数据模型设计",
}
