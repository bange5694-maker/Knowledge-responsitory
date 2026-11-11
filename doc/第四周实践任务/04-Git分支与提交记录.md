# 04 Git 分支与提交记录

> 对应任务：版本管理要求——组员把自己的工作 push 到远程仓库中自己的分支，通知组长合并到 develop，全部完成后由组长合并到 master。
> 记录人：李子涵　|　个人分支：`L_branch`　|　日期：2026-11-11

---

## 一、仓库与分支现状

| 项目 | 值 |
|---|---|
| 远程仓库 | <https://github.com/bange5694-maker/Knowledge-responsitory.git> |
| 默认分支 | `main`（GitHub 仓库当前没有 `master`，也没有 `develop`） |
| 个人分支 | `L_branch`（远程已存在，本次在其上继续提交） |
| 基线 | `main` @ `40ec54e`（2026-11-10「更新数据库初始化脚本」） |
| 个人分支原位置 | `94c1c58`（2026-10-11「Update README.md」，只加了姓名） |

### 为什么先合并 main

`L_branch` 原来停在 10 月 11 日，落后 `main` 很多（缺少 11 月 10 日的 `dailyblog.sql` 更新、何君杰的代码注释、H_branch 的报告等）。如果直接在这个旧基线上写文档，提交上去会和主分支差很多，组长合并时容易冲突。

所以先做了一次同步：

```bash
git switch -c L_branch origin/L_branch
git merge origin/main
```

合并时只有 `README.md` 冲突：`L_branch` 加了「李子涵」，`main` 加了「何君杰」。解决方式是**两行都保留**：

```text
李子涵，2415304652，软件工程6班
何君杰，2415304667，软件工程6班
```

合并提交：`223fc9f 同步 main 分支最新内容，作为第四周实践任务基线`。

---

## 二、本次提交记录

```text
* fce1456 docs(week4): 记录 PR #6 与远程推送结果
* 9e52e7d docs(week4): 修正 nav_node_mobile 递归说明
* 003ac39 docs(week4): 记录分支提交与合并流程
* 03fa288 docs(week4): 复核模板继承/包含关系并重绘UML包图
* f727bb4 docs(week4): 添加主题数据库验证与任务总览
*   223fc9f 同步 main 分支最新内容，作为第四周实践任务基线
|\
| * 40ec54e (origin/main) 更新数据库初始化脚本（知识分享主题测试数据，已脱敏）
...
* 94c1c58 Update README.md
```

| 提交 | 说明 | 主要内容 |
|---|---|---|
| `223fc9f` | 同步 main 分支最新内容，作为第四周实践任务基线 | 把 `L_branch` 更新到 `main` 的最新状态；解决 README 姓名冲突 |
| `f727bb4` | docs(week4): 添加主题数据库验证与任务总览 | `README.md`、`01-数据库初始化与主题数据验证.md` |
| `03fa288` | docs(week4): 复核模板继承/包含关系并重绘UML包图 | `02-模板关系复核与UML包图.md`、`03-界面设计说明书复核记录.md`、`模板关系清单.md`、修正版包图 PNG/SVG、`tools/audit_templates.py` |
| `003ac39` | docs(week4): 记录分支提交与合并流程 | 本文件 |
| `9e52e7d` | docs(week4): 修正 nav_node_mobile 递归说明 | `02-模板关系复核与UML包图.md` 的一处措辞 |
| `fce1456` | docs(week4): 记录 PR #6 与远程推送结果 | 本文件、`README.md` |

作者信息（与仓库里 `L_branch` 原有提交一致）：

```text
李子涵 <3171980688@qq.com>
```

---

## 三、推送与 PR

### 1. 推送个人分支

```bash
git push origin L_branch
```

因为 `origin/L_branch`（`94c1c58`）是当前 `L_branch` 的祖先，这次是普通快进推送，不需要 `--force`。

**推送结果（2026-11-11 已完成）**：

```text
94c1c58..9e52e7d  L_branch -> L_branch   # 首次推送
9e52e7d..fce1456  L_branch -> L_branch   # 补充 PR 记录后
```

PR #6 的 head 会随分支新提交自动更新，以 GitHub 页面显示的最新 commit 为准。

### 2. 在 GitHub 上发 PR

**已创建 PR #6**：

<https://github.com/bange5694-maker/Knowledge-responsitory/pull/6>

- **base**：`main`
- **compare**：`L_branch`
- 标题：`第四周实践任务：数据库主题验证 + 模板关系复核（李子涵）`

如果组长后来建了 `develop`，把 PR 的 base 改成 `develop` 即可。

如果想手动再开一个 PR，也可以打开：

<https://github.com/bange5694-maker/Knowledge-responsitory/compare/main...L_branch?expand=1>

### 3. 通知组长

把 PR 链接发到群里，说明：

> 我的 `L_branch` 已推上去了，新增内容只在 `doc/第四周实践任务/`，没改 settings/migrations/frontend，麻烦合并一下；合并后建议按 `03-界面设计说明书复核记录.md` 修正说明书 5.3/6.1。

---

## 四、与课程要求的差异

课程图片写的是：

```text
组员分支 → develop → master
```

本仓库的实际状态是：

- 默认分支叫 `main`，不是 `master`；
- 目前没有 `develop` 分支；
- 之前的 PR 都是直接合到 `main`（PR #1、#2 的记录仍在）。

### 建议（给组长）

如果老师严格要求 `develop → master`，建议组长在 GitHub 上补一条规范流程：

```bash
# 1. 从 main 建 develop（只做一次）
git switch main
git pull
git switch -c develop
git push -u origin develop

# 2. 组员 PR 的 base 改为 develop
# 3. 全部合并后，组长把 develop 合到 main（main 即课程里的 master）
git switch main
git pull
git merge develop --no-ff -m "第四周：合并 develop 到 main"
git push origin main
```

在老师那边可以说明：**本仓库的 `main` 承担课程里 `master` 的角色**；如果必须出现名为 `master` 的分支，再由组长从 `main` 建 `master` 并设为默认分支，但这样会改变现有 PR 的目标，需全组统一。

> 作为组员，我没有直接在 `main` 上提交，也没有执行 `git merge` 到 `main`；合并动作留给组长。

---

## 五、个人贡献怎么看

老师要求“从每个成员的分支查看每个组员的贡献”。本分支的贡献可以这样查：

1. **GitHub 分支页**：`L_branch` 的提交列表，作者为 `李子涵`；
2. **PR 的 Files changed**：只新增 `doc/第四周实践任务/`，不改业务代码；
3. **本目录**：
   - 数据库：`01-数据库初始化与主题数据验证.md`（导入结果、4 篇文章/3 分类/9 标签/2 评论）；
   - 模板：`02-模板关系复核与UML包图.md` + 修正版包图 + 自动扫描脚本；
   - 说明书：`03-界面设计说明书复核记录.md`（按小组模板填写的检查记录）；
   - 版本管理：本文件。
4. **可复现命令**：
   ```bash
   python doc/第四周实践任务/tools/audit_templates.py --check
   ```
   输出 `38 / 12 / 7 / 11` 即与文档一致。

---

## 六、提交时遵守的几条红线

对照小组《作业分工与操作指南.md》：

| 红线 | 本分支做法 |
|---|---|
| 不直接在 `main` 上改 | ✅ 只在 `L_branch` 提交 |
| 不碰 `djangoblog/settings.py` | ✅ 未修改 |
| 不碰 `blog/migrations/` | ✅ 未修改 |
| 不碰 `frontend/` | ✅ 未修改 |
| 不用 `git add .` | ✅ 按文件/目录显式 add |
| 不把密码、`.env` 提交 | ✅ 文档里用 `-p` 交互输入，未写真实密码 |
| 合并交给组长 | ✅ 只推送个人分支并开 PR |

---

## 七、如果 main 又更新了

在推送前如果发现 `main` 有新提交：

```bash
git fetch origin
git merge origin/main
# 如有冲突，解决后 git add <冲突文件> && git commit
git push origin L_branch
```

不要用 `git push --force` 覆盖远程个人分支；如果确实需要 rebase，先和组长确认。
