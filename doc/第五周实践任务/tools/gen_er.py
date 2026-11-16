# -*- coding: utf-8 -*-
"""生成数据库 E-R 图（Crow's Foot 记法，关键字段版）。

矩形=数据库表，框内列主键/外键/关键字段及类型；1 端画竖线，多端画分叉。
Article 与 Tag 的多对多通过中间表 blog_article_tags 显式表示。
完整字段见说明书 3.2 节表结构。
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_data import ENTITIES

W, H = 1720, 1360
FONT = 17
LINE_H = 22
HEAD_H = 50

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_HTML = os.path.join(ROOT, "tools", "week5-er.html")
OUT_PNG = os.path.join(ROOT, "imgs", "week5-er-diagram.png")

# 框内字段：只列主键、外键、唯一键和关键业务列，完整字段见 3.2 节。
ER_FIELDS = {
    "BlogUser": ["id : bigint PK", "username : varchar(150) UK", "password : varchar(128)",
                 "email : varchar(254)", "is_staff : tinyint", "is_active : tinyint",
                 "nickname : varchar(100)", "source : varchar(100)"],
    "OAuthUser": ["id : bigint PK", "author_id : bigint FK", "openid : varchar(50)",
                  "type : varchar(50)", "email : varchar(50)"],
    "OAuthConfig": ["id : bigint PK", "type : varchar(10) UK", "appkey : varchar(200)",
                    "is_enable : tinyint"],
    "Session": ["session_key : varchar(40) PK", "expire_date : datetime"],
    "Article": ["id : int PK", "title : varchar(200) UK", "author_id : bigint FK",
                "category_id : int FK", "status : varchar(1)", "type : varchar(1)",
                "pub_time : datetime", "views : int", "ai_status : varchar(10)"],
    "Category": ["id : int PK", "name : varchar(30) UK", "parent_category_id : int FK",
                 "slug : varchar(60)"],
    "Tag": ["id : int PK", "name : varchar(30) UK", "slug : varchar(60)"],
    "ArticleTag": ["id : bigint PK", "article_id : int FK", "tag_id : int FK",
                   "UNIQUE(article_id, tag_id)"],
    "Comment": ["id : bigint PK", "article_id : int FK", "author_id : bigint FK",
                "parent_comment_id : bigint FK", "is_enable : tinyint"],
    "CommentReaction": ["id : bigint PK", "comment_id : bigint FK", "user_id : bigint FK",
                        "reaction_type : varchar(10)"],
    "BlogSettings": ["id : bigint PK", "site_name : varchar(200)",
                     "color_scheme : varchar(20)", "comment_need_review : tinyint"],
    "Links": ["id : bigint PK", "name : varchar(30) UK", "link : varchar(200)",
              "sequence : int UK", "show_type : varchar(1)"],
    "SideBar": ["id : bigint PK", "name : varchar(100)", "sequence : int UK",
                "is_enable : tinyint"],
    "commands": ["id : bigint PK", "title : varchar(300)", "command : varchar(2000)"],
    "EmailSendLog": ["id : bigint PK", "emailto : varchar(300)", "send_result : tinyint"],
}

BOXES = {
    "BlogUser": dict(x=60, y=100, w=330),
    "OAuthUser": dict(x=490, y=100, w=330),
    "Session": dict(x=60, y=430, w=330),
    "OAuthConfig": dict(x=490, y=430, w=330),
    "Article": dict(x=870, y=100, w=330),
    "Category": dict(x=1310, y=100, w=330),
    "Tag": dict(x=1310, y=340, w=330),
    "ArticleTag": dict(x=1230, y=500, w=280),
    "Comment": dict(x=870, y=780, w=330),
    "CommentReaction": dict(x=1310, y=780, w=330),
    "BlogSettings": dict(x=60, y=780, w=330),
    "Links": dict(x=490, y=780, w=330),
    "SideBar": dict(x=60, y=960, w=330),
    "commands": dict(x=490, y=960, w=330),
    "EmailSendLog": dict(x=870, y=1160, w=340),
}


def tw(s, fs=FONT):
    return sum(fs if ord(ch) > 0x2E80 else fs * 0.55 for ch in s)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


for name, b in BOXES.items():
    b["h"] = HEAD_H + LINE_H * len(ER_FIELDS[name]) + 10


def rect_edge(box, toward):
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    cx, cy = x + w / 2, y + h / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    tx = (w / 2) / abs(dx) if dx else 1e9
    ty = (h / 2) / abs(dy) if dy else 1e9
    t = min(tx, ty)
    return (cx + dx * t, cy + dy * t)


def norm(v):
    m = math.hypot(v[0], v[1]) or 1
    return (v[0] / m, v[1] / m)


def bar_symbol(p, away, color="#111"):
    """1 端的竖线符号。away 为离开实体的方向。"""
    dx, dy = norm(away)
    px, py = -dy, dx
    cx, cy = p[0] + dx * 5, p[1] + dy * 5
    return (f'<line x1="{cx-px*9:.1f}" y1="{cy-py*9:.1f}" x2="{cx+px*9:.1f}" y2="{cy+py*9:.1f}" '
            f'stroke="{color}" stroke-width="1.8"/>')


def crow_symbol(p, away, color="#111"):
    """多端的分叉符号。away 为离开实体的方向。"""
    dx, dy = norm(away)
    px, py = -dy, dx
    base = (p[0] + dx * 4, p[1] + dy * 4)
    tip = (p[0] + dx * 24, p[1] + dy * 24)
    out = [f'<line x1="{base[0]:.1f}" y1="{base[1]:.1f}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" stroke="{color}" stroke-width="1.6"/>']
    for s in (-1, 0, 1):
        out.append(
            f'<line x1="{base[0]+px*8*s:.1f}" y1="{base[1]+py*8*s:.1f}" '
            f'x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" stroke="{color}" stroke-width="1.6"/>'
        )
    return "".join(out)


def card_text(x, y, text):
    w = tw(text, FONT - 5) + 8
    return (f'<rect x="{x-w/2:.1f}" y="{y-13:.1f}" width="{w:.1f}" height="18" fill="#fff" opacity="0.95"/>'
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{FONT-5}" text-anchor="middle" fill="#111">{text}</text>')


RELATIONS = [
    # name, a, b, a_card, b_card, a_route, b_route, dashed, label_pos
    dict(name="绑定", a="BlogUser", b="OAuthUser", a_card="1", b_card="0..*",
         a_route=[], b_route=[], dashed=False, label_pos=(435, 168)),
    dict(name="登录会话", a="BlogUser", b="Session", a_card="1", b_card="0..*",
         a_route=[], b_route=[], dashed=True, label_pos=(285, 380)),
    dict(name="撰写", a="BlogUser", b="Article", a_card="1", b_card="0..*",
         a_route=[(410, 300), (410, 360), (830, 360), (830, 300)], b_route=[],
         dashed=False, label_pos=(620, 348)),
    dict(name="归属", a="Category", b="Article", a_card="1", b_card="0..*",
         a_route=[], b_route=[], dashed=False, label_pos=(1255, 172)),
    dict(name="发表", a="BlogUser", b="Comment", a_card="1", b_card="0..*",
         a_route=[(410, 280), (410, 600), (825, 600), (825, 780)], b_route=[],
         dashed=False, label_pos=(460, 620)),
    dict(name="所属文章", a="Article", b="Comment", a_card="1", b_card="0..*",
         a_route=[], b_route=[], dashed=False, label_pos=(1065, 560)),
    dict(name="包含", a="Article", b="ArticleTag", a_card="1", b_card="0..*",
         a_route=[(1215, 300), (1215, 540)], b_route=[], dashed=False, label_pos=(1255, 430)),
    dict(name="标注", a="Tag", b="ArticleTag", a_card="1", b_card="0..*",
         a_route=[], b_route=[], dashed=False, label_pos=(1510, 470)),
    dict(name="针对", a="Comment", b="CommentReaction", a_card="1", b_card="0..*",
         a_route=[], b_route=[], dashed=False, label_pos=(1255, 838)),
]

SELF_LOOPS = [
    dict(name="父子分类", a="Category", a_card="1", b_card="0..*",
         route=[(1420, 242), (1420, 286), (1530, 286), (1530, 242)],
         label_pos=(1475, 304), card_a=(1435, 258), card_b=(1515, 258)),
    dict(name="父评论", a="Comment", a_card="1", b_card="0..*",
         route=[(950, 944), (950, 986), (1050, 986), (1050, 944)],
         label_pos=(1000, 1004), card_a=(968, 968), card_b=(1032, 968)),
]


def draw_box(name):
    b = BOXES[name]
    e = ENTITIES[name]
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#111" stroke-width="1.8"/>',
        f'<line x1="{x}" y1="{y+HEAD_H}" x2="{x+w}" y2="{y+HEAD_H}" stroke="#111" stroke-width="1.2"/>',
        f'<text x="{x+w/2}" y="{y+21}" font-size="{FONT}" font-weight="bold" text-anchor="middle" fill="#111">{esc(name)}（{esc(e["cn"])}）</text>',
        f'<text x="{x+w/2}" y="{y+39}" font-size="{FONT-6}" text-anchor="middle" fill="#555">{esc(e["table"])}</text>',
    ]
    for i, f in enumerate(ER_FIELDS[name]):
        out.append(f'<text x="{x+12}" y="{y+HEAD_H+19+i*LINE_H}" font-size="{FONT-2}" fill="#111">{esc(f)}</text>')
    return out


parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']

# 先画线，后画框，避免线压住表框
for rel in RELATIONS:
    a, b = rel["a"], rel["b"]
    style = ' stroke-dasharray="8,5"' if rel["dashed"] else ""
    # a 侧
    if rel["a_route"]:
        start = rect_edge(BOXES[a], rel["a_route"][0])
        pts_a = [start] + rel["a_route"]
        end_a = rect_edge(BOXES[b], pts_a[-1])
        pts_a.append(end_a)
    else:
        start = rect_edge(BOXES[a], (BOXES[b]["x"] + BOXES[b]["w"]/2, BOXES[b]["y"] + BOXES[b]["h"]/2))
        end_a = rect_edge(BOXES[b], start)
        pts_a = [start, end_a]
    parts.append(f'<polyline points="{" ".join(f"{px:.1f},{py:.1f}" for px,py in pts_a)}" fill="none" stroke="#222" stroke-width="1.7"{style}/>')
    # 两端符号：away 为离开实体的方向
    away_a = norm((pts_a[1][0] - pts_a[0][0], pts_a[1][1] - pts_a[0][1]))
    away_b = norm((pts_a[-2][0] - pts_a[-1][0], pts_a[-2][1] - pts_a[-1][1]))
    parts.append(bar_symbol(pts_a[0], away_a) if rel["a_card"] == "1" else crow_symbol(pts_a[0], away_a))
    parts.append(bar_symbol(pts_a[-1], away_b) if rel["b_card"] == "1" else crow_symbol(pts_a[-1], away_b))
    # 关系名
    lx, ly = rel["label_pos"]
    lw = tw(rel["name"], FONT - 2) + 16
    parts.append(f'<rect x="{lx-lw/2:.1f}" y="{ly-15:.1f}" width="{lw:.1f}" height="22" fill="#fff" opacity="0.95"/>')
    parts.append(f'<text x="{lx}" y="{ly}" font-size="{FONT-2}" text-anchor="middle" fill="#111">{esc(rel["name"])}</text>')
    # 重数文字
    def card_xy(p, away):
        dx, dy = away
        if abs(dx) >= abs(dy):
            return (p[0] + dx * 28, p[1] - 12)
        return (p[0] + 16, p[1] + dy * 28)
    ax, ay = card_xy(pts_a[0], away_a)
    bx, by = card_xy(pts_a[-1], away_b)
    parts.append(card_text(ax, ay, rel["a_card"]))
    parts.append(card_text(bx, by, rel["b_card"]))

# 自关联
for loop in SELF_LOOPS:
    a = loop["a"]
    route = loop["route"]
    pts = [rect_edge(BOXES[a], route[0])] + route
    pts.append(rect_edge(BOXES[a], route[-1]))
    parts.append(f'<polyline points="{" ".join(f"{px:.1f},{py:.1f}" for px,py in pts)}" fill="none" stroke="#222" stroke-width="1.7"/>')
    away_a = norm((pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]))
    away_b = norm((pts[-2][0] - pts[-1][0], pts[-2][1] - pts[-1][1]))
    parts.append(bar_symbol(pts[0], away_a))
    parts.append(crow_symbol(pts[-1], away_b))
    lx, ly = loop["label_pos"]
    lw = tw(loop["name"], FONT - 2) + 16
    parts.append(f'<rect x="{lx-lw/2:.1f}" y="{ly-15:.1f}" width="{lw:.1f}" height="22" fill="#fff" opacity="0.95"/>')
    parts.append(f'<text x="{lx}" y="{ly}" font-size="{FONT-2}" text-anchor="middle" fill="#111">{esc(loop["name"])}</text>')
    parts.append(card_text(loop["card_a"][0], loop["card_a"][1], loop["a_card"]))
    parts.append(card_text(loop["card_b"][0], loop["card_b"][1], loop["b_card"]))

# 表框最后画
for name in BOXES:
    parts.extend(draw_box(name))

# 图例
legend = ("矩形=数据库表；框内为关键字段及类型（PK=主键，FK=外键，UK=唯一）；"
          "1 端竖线，多端分叉；虚线=逻辑关联；完整字段见 3.2 节表结构。")
parts.append(f'<text x="40" y="{H-20}" font-size="{FONT-2}" fill="#333">{esc(legend)}</text>')

svg = "\n".join(parts)
html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:0;background:#fff}} text{{font-family:"Microsoft YaHei","SimHei",sans-serif}}
</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg}</svg></body></html>'''
with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("ER HTML:", OUT_HTML)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if os.path.exists(CHROME):
    subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--window-size={W},{H}", "--force-device-scale-factor=2",
        f"--screenshot={OUT_PNG}", "file:///" + OUT_HTML.replace("\\", "/"),
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("PNG:", OUT_PNG)
else:
    print("Chrome not found")
