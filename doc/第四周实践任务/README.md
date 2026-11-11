# 第四周实践任务 · 个人交付（李子涵）

> **分支**：`L_branch`　|　**学号**：2415304652　|　**组别**：13 组（软件工程 6 班）
> **基线**：`main`（已同步 2026-11-10 的 `dailyblog.sql` 和最新文档）
> **仓库**：<https://github.com/bange5694-maker/Knowledge-responsitory>

小组仓库里已经有一套可运行的 DjangoBlog（「知识分享」主题），所以本分支**不重写网站**，而是把自己在第四周负责的数据库验证、模板关系复核、界面说明书检查和 Git 流程做成可检查、可复现的交付物。

---

## 一、任务对照

图片里红线圈出的要求，与本分支的对应关系如下：

| 图片中的要求 | 本分支对应内容 | 状态 |
|---|---|---|
| （1）初始化数据库、选定博客主题，将所有测试数据根据主题实例化 | [`01-数据库初始化与主题数据验证.md`](01-数据库初始化与主题数据验证.md)：在干净库中导入 `dailyblog.sql`，逐表核对 4 篇文章、3 个分类、9 个标签、2 条评论 | 已验证 |
| （2）分析说明系统的用例和界面流转关系 | 沿用小组 [`doc/界面设计说明书.md`](../界面设计说明书.md) 第 3、4 章（13 张界面截屏、11 条流转路径、思维导图） | 小组已完成，本次引用 |
| （3）分析模板功能、模板之间/模板与 tag 的继承与包含关系，使用 UML 包图绘制 | [`02-模板关系复核与UML包图.md`](02-模板关系复核与UML包图.md)：扫描 38 个模板、12 条继承、7 条包含、11 个包含标签；修正说明书 5.3/6.1 的错误并重绘包图 | 已复核并修正 |
| （4）形成文档，按模板撰写界面设计说明书，上传到 doc，最终合并到 master | 说明书已在 `doc/`；本分支新增复核记录 [`03-界面设计说明书复核记录.md`](03-界面设计说明书复核记录.md)，待组长合并 | 文档已就位，待合并 |
| 版本管理：成员 push 自己的分支 → 组长合并 develop → master | [`04-Git分支与提交记录.md`](04-Git分支与提交记录.md)：`L_branch` 提交记录、推送/PR/合并步骤、与小组现行 `main` 流程的差异说明 | 已按个人分支提交 |

> 课程要求写的是 `develop → master`；本仓库实际默认分支是 `main`，目前**没有 `develop` 分支**。本分支按小组现行约定以 `main` 为集成分支；如果老师严格要求 `develop`，请组长先建 `develop`，再按 04 文档的流程合并。

---

## 二、交付物清单

| 文件 | 内容 |
|---|---|
| [`01-数据库初始化与主题数据验证.md`](01-数据库初始化与主题数据验证.md) | 主题定义、导入命令、逐表行数、文章/评论/标签清单、截图与注意事项 |
| [`02-模板关系复核与UML包图.md`](02-模板关系复核与UML包图.md) | 12 条继承、7 条包含、11 个包含标签的扫描结果；5 处文档偏差；修正版 UML 包图 |
| [`03-界面设计说明书复核记录.md`](03-界面设计说明书复核记录.md) | 按小组“检查记录模板”填写的正式复核记录，可直接交给组长/席佳宁 |
| [`04-Git分支与提交记录.md`](04-Git分支与提交记录.md) | 分支模型、提交列表、push 与 PR 命令、合并注意事项 |
| [`模板关系清单.md`](模板关系清单.md) | 由脚本自动生成的完整清单（38 个模板的继承/包含/标签关系） |
| [`imgs/template-packages-corrected.png`](imgs/template-packages-corrected.png) | 修正版模板关系 UML 包图（1800×1120） |
| [`imgs/template-packages-corrected.svg`](imgs/template-packages-corrected.svg) | 包图矢量源文件，便于继续修改 |
| [`tools/audit_templates.py`](tools/audit_templates.py) | 模板关系静态扫描脚本，不依赖 Django/数据库 |

---

## 三、10 分钟验收

### 1. 看模板关系是否与代码一致（无需环境）

在仓库根目录执行：

```bash
python doc/第四周实践任务/tools/audit_templates.py --check
```

期望输出：

```text
统计： {'templates': 38, 'extends': 12, 'includes': 7, 'inclusion_tags': 11}
校验通过。
```

再打开 [`imgs/template-packages-corrected.png`](imgs/template-packages-corrected.png)，对照 [`02-模板关系复核与UML包图.md`](02-模板关系复核与UML包图.md) 的“五处偏差”阅读。

### 2. 看数据库脚本能否初始化主题数据（可选，需要 MySQL）

```bash
mysql -u root -p -e "CREATE DATABASE dailyblog_week4_verify CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql --default-character-set=utf8mb4 -u root -p dailyblog_week4_verify < dailyblog.sql
```

然后查行数：

```sql
SELECT COUNT(*) FROM blog_article;       -- 4
SELECT COUNT(*) FROM blog_category;      -- 3
SELECT COUNT(*) FROM blog_tag;           -- 9
SELECT COUNT(*) FROM comments_comment;   -- 2
```

详细输出和截图见 [`01-数据库初始化与主题数据验证.md`](01-数据库初始化与主题数据验证.md)。

### 3. 看说明书复核结论

打开 [`03-界面设计说明书复核记录.md`](03-界面设计说明书复核记录.md)，重点看“三、发现的问题”与“五、给组长/席佳宁的修改建议”。

---

## 四、本分支相对 `main` 改了什么

合并 `main` 后，本分支相对 `main` 只多出：

- `doc/第四周实践任务/` 整个目录（本文档、3 份说明、清单、包图、扫描脚本）；
- `README.md` 中保留双方姓名（解决冲突时把 `李子涵` 与 `何君杰` 两行都留下）。

**没有修改**：`djangoblog/settings.py`、`blog/migrations/`、`frontend/`、数据库结构、任何业务代码。因此组长合并时不会产生代码冲突。

---

## 五、给组长的一句话

> 请把 `L_branch` 合并到 `main`（或按课程要求先建 `develop` 再合并）。新增内容全部在 `doc/第四周实践任务/`，不会和别人的代码冲突。合并后建议按 [`03-界面设计说明书复核记录.md`](03-界面设计说明书复核记录.md) 修正说明书 5.3/6.1 的 5 处偏差；修正版包图已经画好，可直接替换 `doc/imgs/diagrams/diagram-03-packages.png`。

---

## 六、提交信息

- 作者：李子涵 `<3171980688@qq.com>`
- 分支：`L_branch`（个人分支，不直接改 `main`）
- 提交记录：见 [`04-Git分支与提交记录.md`](04-Git分支与提交记录.md)
