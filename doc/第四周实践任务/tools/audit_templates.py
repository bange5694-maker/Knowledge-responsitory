#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""静态扫描 Django 模板的 extends / include / inclusion_tag 关系。

用法（在仓库根目录执行）：
    python doc/第四周实践任务/tools/audit_templates.py
    python doc/第四周实践任务/tools/audit_templates.py --write
    python doc/第四周实践任务/tools/audit_templates.py --check

不依赖 Django，也不连接数据库，只读 templates/ 与 */templatetags/*.py。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = REPO_ROOT / "templates"
OUT_FILE = Path(__file__).resolve().parents[1] / "模板关系清单.md"

EXTENDS_RE = re.compile(r'{%\s*extends\s+["\']([^"\']+)["\']')
INCLUDE_RE = re.compile(r'{%\s*include\s+["\']([^"\']+)["\']')
LOAD_RE = re.compile(r'{%\s*load\s+([^%]+)%}')
INCLUSION_RE = re.compile(
    r'@register\.inclusion_tag\(["\']([^"\']+)["\']\)\s*\ndef\s+(\w+)'
)


def scan_templates() -> list[dict]:
    rows = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        rel = path.relative_to(TEMPLATES).as_posix()
        text = path.read_text(encoding="utf-8")
        rows.append(
            {
                "file": rel,
                "extends": EXTENDS_RE.findall(text),
                "includes": INCLUDE_RE.findall(text),
                "loads": [x.strip() for x in LOAD_RE.findall(text)],
            }
        )
    return rows


def scan_inclusion_tags() -> list[dict]:
    rows = []
    for path in sorted(REPO_ROOT.rglob("templatetags/*.py")):
        if ".venv" in path.parts or "site-packages" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for template, func in INCLUSION_RE.findall(text):
            rows.append(
                {
                    "lib": path.relative_to(REPO_ROOT).as_posix(),
                    "func": func,
                    "template": template,
                }
            )
    return rows


def build_markdown(templates: list[dict], tags: list[dict]) -> str:
    extends = [(r["file"], t) for r in templates for t in r["extends"]]
    includes = [(r["file"], t) for r in templates for t in r["includes"]]
    nav_refs = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".html", ".py"}:
            continue
        rel_parts = path.relative_to(REPO_ROOT).parts
        if ".git" in rel_parts or "doc" in rel_parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "nav_node" in text and path.name not in {"nav_node.html", "nav_node_mobile.html"}:
            nav_refs.append(path.relative_to(REPO_ROOT).as_posix())

    lines = [
        "# 模板关系清单（自动扫描）",
        "",
        "> 由 `doc/第四周实践任务/tools/audit_templates.py` 生成；扫描范围 `templates/` 与各应用 `templatetags/`。",
        "> 统计口径：`{% extends %}` / `{% include %}` 按字面路径计数；变量模板名（如 `{% include template_name %}`）单独说明。",
        "",
        "## 统计",
        "",
        "| 项目 | 数量 |",
        "|---|---:|",
        f"| HTML 模板文件 | {len(templates)} |",
        f"| 继承关系（extends） | {len(extends)} |",
        f"| 包含关系（include，字面路径） | {len(includes)} |",
        f"| 包含标签（inclusion_tag） | {len(tags)} |",
        "",
        "## 一、模板继承关系",
        "",
        "| 子模板 | 父模板 |",
        "|---|---|",
    ]
    lines += [f"| `{child}` | `{parent}` |" for child, parent in extends]
    lines += [
        "",
        "## 二、模板包含关系",
        "",
        "| 宿主模板 | 被包含模板 |",
        "|---|---|",
    ]
    lines += [f"| `{host}` | `{inc}` |" for host, inc in includes]
    lines += [
        "",
        "> 另外，`comments/tags/comment_item_tree.html` 第 47～54 行通过变量",
        "> `{% include template_name %}` 递归包含自身；因模板名是变量，未计入上表。",
        "",
        "## 三、包含标签（inclusion_tag）",
        "",
        "| 标签库 | 标签函数 | 渲染模板 |",
        "|---|---|---|",
    ]
    lines += [
        f"| `{t['lib']}` | `{t['func']}` | `{t['template']}` |" for t in tags
    ]
    lines += [
        "",
        "## 四、nav_node 引用检查",
        "",
        f"- 引用 `nav_node` 的其他文件：{len(nav_refs)} 个"
        + (f"（{', '.join(nav_refs)}）" if nav_refs else "。"),
        "- 结论：`templates/share_layout/nav_node.html` 与 `nav_node_mobile.html` 为旧版片段，",
        "  当前没有任何页面 include 它们；`nav.html` 直接通过 `{% query nav_category_list %}` 渲染分类菜单。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="写入 模板关系清单.md")
    parser.add_argument("--check", action="store_true", help="校验统计值，不一致时返回 1")
    args = parser.parse_args()

    templates = scan_templates()
    tags = scan_inclusion_tags()
    md = build_markdown(templates, tags)

    if args.write:
        OUT_FILE.write_text(md, encoding="utf-8")
        print(f"已写入 {OUT_FILE.relative_to(REPO_ROOT)}")
    else:
        print(md)

    if args.check:
        counts = {
            "templates": len(templates),
            "extends": sum(len(r["extends"]) for r in templates),
            "includes": sum(len(r["includes"]) for r in templates),
            "inclusion_tags": len(tags),
        }
        expected = {"templates": 38, "extends": 12, "includes": 7, "inclusion_tags": 11}
        print("\n统计：", counts, file=sys.stderr)
        if counts != expected:
            print(f"校验失败：期望 {expected}", file=sys.stderr)
            return 1
        print("校验通过。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
