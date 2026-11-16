# -*- coding: utf-8 -*-
"""生成 UML 数据模型类图（关键字段版）。

图为概念级类图：只画主键、外键、唯一键和关键业务字段，完整字段见说明书 3.2 节。
输出 HTML/SVG，再用无头 Chrome 截图为 PNG。
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_data import ENTITIES, GROUPS

W, H = 1720, 1440
FONT = 18
LINE_H = 22
HEAD_H = 42

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_HTML = os.path.join(ROOT, "tools", "week5-class.html")
OUT_PNG = os.path.join(ROOT, "imgs", "week5-class-diagram.png")

PACKAGES = [
    (40, 40, 790, 640, "D1 账户与权限数据"),
    (840, 40, 820, 640, "D2 内容数据"),
    (840, 720, 820, 340, "D3 评论数据"),
    (40, 720, 790, 680, "D4 配置数据"),
    (840, 1100, 820, 240, "D5 日志数据"),
]

CLASSES = {
    "BlogUser": dict(x=60, y=100, w=320),
    "OAuthUser": dict(x=490, y=100, w=320),
    "Session": dict(x=60, y=430, w=320),
    "OAuthConfig": dict(x=490, y=430, w=320),
    "Article": dict(x=870, y=100, w=330),
    "Category": dict(x=1310, y=100, w=330),
    "Tag": dict(x=1310, y=340, w=330),
    "Comment": dict(x=870, y=780, w=330),
    "CommentReaction": dict(x=1310, y=780, w=330),
    "BlogSettings": dict(x=60, y=780, w=320),
    "Links": dict(x=490, y=780, w=320),
    "SideBar": dict(x=60, y=960, w=320),
    "commands": dict(x=490, y=960, w=320),
    "EmailSendLog": dict(x=870, y=1160, w=340),
}


def tw(s, fs=FONT):
    return sum(fs if ord(ch) > 0x2E80 else fs * 0.55 for ch in s)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


for name, c in CLASSES.items():
    c["h"] = HEAD_H + LINE_H * len(ENTITIES[name]["key_fields"]) + 12


def anchor(name, toward):
    c = CLASSES[name]
    x, y, w, h = c["x"], c["y"], c["w"], c["h"]
    cx, cy = x + w / 2, y + h / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    tx = (w / 2) / abs(dx) if dx else 1e9
    ty = (h / 2) / abs(dy) if dy else 1e9
    t = min(tx, ty)
    return (cx + dx * t, cy + dy * t)


def polyline(a, b, waypoints):
    if waypoints:
        pts = [anchor(a, waypoints[0])] + waypoints + [anchor(b, waypoints[-1])]
    else:
        pa = (CLASSES[a]["x"] + CLASSES[a]["w"] / 2, CLASSES[a]["y"] + CLASSES[a]["h"] / 2)
        pb = (CLASSES[b]["x"] + CLASSES[b]["w"] / 2, CLASSES[b]["y"] + CLASSES[b]["h"] / 2)
        p0 = anchor(a, pb)
        pts = [p0, anchor(b, p0)]
    return pts


ASSOCS = [
    # a, b, label, card_a, card_b, waypoints, dashed
    ("BlogUser", "OAuthUser", "绑定", "1", "0..*", [], False),
    ("BlogUser", "Session", "登录会话", "1", "0..*", [], True),
    ("BlogUser", "Article", "撰写", "1", "0..*", [(390, 340), (830, 340), (830, 300)], False),
    ("Category", "Article", "归属", "1", "0..*", [], False),
    ("Article", "Tag", "标注", "0..*", "0..*", [], False),
    ("BlogUser", "Comment", "发表", "1", "0..*", [(410, 280), (410, 600), (900, 600), (900, 780)], False),
    ("Article", "Comment", "所属文章", "1", "0..*", [], False),
    ("Comment", "CommentReaction", "针对", "1", "0..*", [], False),
]


def label_box(x, y, text, fs=FONT - 2):
    w = tw(text, fs) + 12
    return (
        f'<rect x="{x - w/2:.1f}" y="{y - 15:.1f}" width="{w:.1f}" height="22" fill="#fff" opacity="0.94"/>'
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs}" text-anchor="middle" fill="#111">{esc(text)}</text>'
    )


parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']

# 包
for (x, y, w, h, title) in PACKAGES:
    parts.append(
        f'<path d="M {x} {y+26} L {x} {y} L {x+250} {y} L {x+250} {y+26} L {x+w} {y+26} '
        f'L {x+w} {y+h} L {x} {y+h} Z" fill="#fbfbfb" stroke="#666" stroke-width="1.6"/>'
    )
    parts.append(f'<text x="{x+12}" y="{y+19}" font-size="{FONT}" font-weight="bold" fill="#111">{esc(title)}</text>')

# 关联线
for (a, b, label, ca, cb, wps, dashed) in ASSOCS:
    pts = polyline(a, b, wps)
    style = ' stroke-dasharray="8,5"' if dashed else ""
    parts.append(
        f'<polyline points="{" ".join(f"{px:.1f},{py:.1f}" for px,py in pts)}" '
        f'fill="none" stroke="#222" stroke-width="1.7"{style}/>'
    )
    # 关系名放在中间段
    mid = len(pts) // 2
    ax, ay = pts[mid - 1]
    bx, by = pts[mid]
    lx, ly = (ax + bx) / 2, (ay + by) / 2
    if abs(bx - ax) > abs(by - ay):
        ly -= 12
    else:
        lx += 55
    if label == "发表":
        lx, ly = 460, 625
    parts.append(label_box(lx, ly, label))
    # 多重性：取首尾两段
    def mult(p, q, text, end):
        dx, dy = q[0] - p[0], q[1] - p[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        sign = 1 if end == "start" else -1
        return (p[0] + nx * 20 * sign + (10 if abs(dx) > abs(dy) else 0),
                p[1] + ny * 20 * sign - (14 if abs(dx) > abs(dy) else 0), text)
    for mx, my, t in [mult(pts[0], pts[1], ca, "start"), mult(pts[-1], pts[-2], cb, "end")]:
        parts.append(f'<text x="{mx:.1f}" y="{my:.1f}" font-size="{FONT-4}" text-anchor="middle" fill="#111">{t}</text>')

# 自关联：Category 父子分类（画在 Category 下方）
cx, cy = 1475, 242
parts.append(
    f'<polyline points="{cx},{cy} {cx},{cy+30} {cx+90},{cy+30} {cx+90},{cy}" '
    f'fill="none" stroke="#222" stroke-width="1.7"/>'
)
parts.append(label_box(cx + 45, cy + 46, "父子分类"))
parts.append(f'<text x="{cx+18}" y="{cy+14}" font-size="{FONT-4}" text-anchor="middle" fill="#111">1</text>')
parts.append(f'<text x="{cx+72}" y="{cy+14}" font-size="{FONT-4}" text-anchor="middle" fill="#111">0..*</text>')

# 自关联：Comment 父评论（画在 Comment 下方）
cx, cy = 1010, 944
parts.append(
    f'<polyline points="{cx},{cy} {cx},{cy+30} {cx+90},{cy+30} {cx+90},{cy}" '
    f'fill="none" stroke="#222" stroke-width="1.7"/>'
)
parts.append(label_box(cx + 45, cy + 46, "父评论"))
parts.append(f'<text x="{cx+18}" y="{cy+14}" font-size="{FONT-4}" text-anchor="middle" fill="#111">1</text>')
parts.append(f'<text x="{cx+72}" y="{cy+14}" font-size="{FONT-4}" text-anchor="middle" fill="#111">0..*</text>')

# 类框
for name, c in CLASSES.items():
    x, y, w, h = c["x"], c["y"], c["w"], c["h"]
    e = ENTITIES[name]
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#111" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x}" y1="{y+HEAD_H}" x2="{x+w}" y2="{y+HEAD_H}" stroke="#111" stroke-width="1.3"/>')
    title = f'{name}（{e["cn"]}）'
    parts.append(f'<text x="{x+w/2}" y="{y+27}" font-size="{FONT}" font-weight="bold" text-anchor="middle" fill="#111">{esc(title)}</text>')
    for i, field in enumerate(e["key_fields"]):
        parts.append(f'<text x="{x+12}" y="{y+HEAD_H+20+i*LINE_H}" font-size="{FONT-2}" fill="#111">{esc(field)}</text>')

# 图例
legend = "字段格式：字段名（PK/FK/UK）  |  PK=主键，FK=外键，UK=唯一  |  虚线=逻辑关联  |  完整字段见 3.2 节表结构"
parts.append(f'<text x="40" y="{H-20}" font-size="{FONT-2}" fill="#333">{esc(legend)}</text>')

svg = "\n".join(parts)
html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:0;background:#fff}} text{{font-family:"Microsoft YaHei","SimHei",sans-serif}}
</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg}</svg></body></html>'''
with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

# 碰撞检查：关联线是否穿过非端点类框
def seg_rect(pts, box):
    x, y, w, h = box
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        for k in range(101):
            t = k / 100
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            if x - 1 <= px <= x + w + 1 and y - 1 <= py <= y + h + 1:
                return True
    return False


print("=== 类图碰撞检查 ===")
issues = 0
for (a, b, label, ca, cb, wps, dashed) in ASSOCS:
    pts = polyline(a, b, wps)
    for name, c in CLASSES.items():
        if name in (a, b):
            continue
        if seg_rect(pts, (c["x"], c["y"], c["w"], c["h"])):
            print(f"  关联 {a}-{b}（{label}）穿过 {name}")
            issues += 1
print("  无穿框" if not issues else f"  共 {issues} 处穿框")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if os.path.exists(CHROME):
    subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--window-size={W},{H}", "--force-device-scale-factor=2",
        f"--screenshot={OUT_PNG}", "file:///" + OUT_HTML.replace("\\", "/"),
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("PNG:", OUT_PNG)
else:
    print("Chrome not found; HTML only:", OUT_HTML)
