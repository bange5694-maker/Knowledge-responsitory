# 第五周实践任务：数据模型设计说明书

## 交付物

- `数据模型设计说明书.docx`：按老师提供的《文档模板-软件数据模型设计说明书模板》样式生成，含标题区、3 个章节、2 张图、20 张表。
- `数据模型设计说明书.md`：与 docx 同内容的 Markdown 源稿，便于快速检索和 diff。
- `imgs/week5-er-diagram.png`：数据库 E-R 图（Crow's Foot 记法，含 `blog_article_tags` 中间表）。
- `imgs/week5-class-diagram.png`：UML 数据模型类图（按 D1–D5 五个数据域分包）。

## 建模依据与范围

- 依据线上 `main` 分支 commit `81f2d69` 的 `models.py`；该提交的数据模型与本地 `D_branch` 一致。
- 正文覆盖 13 个业务 model、Django 内置 `django_session` 辅助表和 `blog_article_tags` 中间表。
- Django 内置权限表（`auth_group`、`auth_permission`）、后台日志表（`django_admin_log`）、站点表（`django_site`）属于框架基础设施，未在正文展开；`BlogUser.groups`、`user_permissions` 只在关系表中说明。
- AI 字段与 `djangoblog.ai.client` 已在 `main@81f2d69`；站内问答的检索、接口和页面实现目前只在 `D_branch`，文中已单独标注。

## 文件说明

- `tools/model_data.py`：单一事实源。实体、字段、类型、约束、关系、功能矩阵都写在这里；改字段先改此文件。
- `tools/content.py`：文档内容块（章节、表格、图注）。
- `tools/gen_er.py`：生成 E-R 图 HTML/SVG，并调用无头 Chrome 截图 PNG。
- `tools/gen_class.py`：生成 UML 类图 HTML/SVG，并调用无头 Chrome 截图 PNG。
- `tools/render_md.py`：渲染 Markdown 源稿。
- `tools/render_docx.py`：按模板样式生成 docx（A4、宋体/Times New Roman、表头重复、小表尽量不拆页）。
- `tools/check_models.py`：把 `model_data.py` 与 Django `models.py` 的字段名、数据库列类型逐项对比。

## 重新生成

在仓库根目录执行（使用项目虚拟环境；脚本内部按自身路径定位输出，不依赖 cwd）：

```bash
.venv/Scripts/python.exe doc/第五周实践任务/tools/gen_er.py
.venv/Scripts/python.exe doc/第五周实践任务/tools/gen_class.py
.venv/Scripts/python.exe doc/第五周实践任务/tools/render_md.py
.venv/Scripts/python.exe doc/第五周实践任务/tools/render_docx.py
```

可选：转 PDF 做版式检查（需要 LibreOffice）：

```bash
"/c/Users/Lenovo/AppData/Local/Programs/LibreOffice/program/soffice.exe" \
  --headless --convert-to pdf --outdir doc/第五周实践任务 "doc/第五周实践任务/数据模型设计说明书.docx"
```

字段/类型校验：

```bash
.venv/Scripts/python.exe doc/第五周实践任务/tools/check_models.py
```

## 说明

- 两张图只画主键、外键、唯一键和关键字段；完整字段以 3.2 节表结构为准。
- 表结构按数据库实际列列出，包含继承字段；类型按 Django 5.2 + MySQL 的迁移结果标注。
- 为避免连线交叉，E-R 图和类图没有画出 `OAuthConfig—OAuthUser` 的逻辑关联、`BlogUser—CommentReaction` 的回应关系和权限关联，完整关系见表 3-1。
- `_preview/`、`*.pdf` 和 `tools/*.html` 是本地预览产物，不提交。
