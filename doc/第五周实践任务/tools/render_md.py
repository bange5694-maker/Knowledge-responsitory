# -*- coding: utf-8 -*-
"""把 content.BLOCKS 渲染为 Markdown 源稿。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import BLOCKS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "数据模型设计说明书.md")


def md_escape(s):
    return str(s).replace("|", "\\|").replace("\n", "<br>")


def render_table(caption, headers, rows, widths):
    out = []
    if caption:
        out.append(f"**{caption}**")
        out.append("")
    out.append("| " + " | ".join(md_escape(h) for h in headers) + " |")
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(md_escape(c) for c in row) + " |")
    out.append("")
    return "\n".join(out)


def main():
    out = []
    for block in BLOCKS:
        kind = block[0]
        if kind == "title":
            out.append(f"# {block[1]}")
            out.append("")
        elif kind == "center":
            out.append(f"<p align=\"center\">{block[1]}</p>")
            out.append("")
        elif kind == "h1":
            out.append(f"## {block[1]}")
            out.append("")
        elif kind == "h2":
            out.append(f"### {block[1]}")
            out.append("")
        elif kind == "p":
            out.append(block[1])
            out.append("")
        elif kind == "note":
            out.append(f"> 注：{block[1]}")
            out.append("")
        elif kind == "bullet":
            out.append(f"- {block[1]}")
        elif kind == "table":
            out.append(render_table(block[1], block[2], block[3], block[4]))
        elif kind == "figure":
            path, caption = block[1], block[2]
            out.append(f"![{caption}]({path.replace(os.sep, '/')})")
            out.append("")
            out.append(f"<p align=\"center\">{caption}</p>")
            out.append("")
            if len(block) > 4 and block[4]:
                out.append(f"> {block[4]}")
                out.append("")
        elif kind == "pagebreak":
            out.append("---")
            out.append("")
        elif kind == "section":
            pass
    text = "\n".join(out).rstrip() + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("Markdown:", OUT, len(text), "chars")


if __name__ == "__main__":
    main()
