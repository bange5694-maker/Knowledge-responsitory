# -*- coding: utf-8 -*-
"""DjangoBlog 用例图参考图生成器：精确坐标 + 碰撞检测 + SVG/HTML 输出。
坐标约定：粉笔手绘可完全照抄此布局。"""
import math, json

W, H = 1680, 1400
BX1, BY1, BX2, BY2 = 250, 70, 1430, 1340   # 系统边界框
FONT = 17
RY = 32

def tw(s):  # 文本宽度估算：中文按字号，ASCII 按半宽
    w = 0
    for ch in s:
        w += FONT if ord(ch) > 0x2e80 else FONT*0.52
    return w

def ell(s):
    return max(72.0, tw(s)/2 + 26), RY   # rx, ry

actors = {
    'Guest':  ('访客',         96, 250),
    'User':   ('注册用户',     96, 620),
    'Admin':  ('管理员',       96, 1090),
    'OAuth':  ('第三方登录平台', 1520, 470),
    'Mail':   ('邮件服务器',   1520, 590),
    'WeChat': ('微信服务器',   1520, 1180),
}

ucs = {
    # 访客
    'U1':  ('搜索文章',      490, 140),
    'U2':  ('浏览文章列表',  830, 160),
    'U3':  ('按分类浏览',   1150, 160),
    'U4':  ('查看文章详情',  490, 380),
    'U5':  ('查看友情链接',  830, 300),
    'U6':  ('按标签浏览',   1150, 300),
    # 注册用户
    'U7':  ('注册',          490, 470),
    'U8':  ('用户登录',      830, 470),
    'U9':  ('第三方登录',   1150, 470),
    'U10': ('补充邮箱',     1330, 380),
    'U11': ('找回密码',      490, 590),
    'U12': ('发送验证邮件', 1150, 590),
    'U13': ('退出登录',      490, 710),
    'U14': ('发表评论',      830, 710),
    'U15': ('回复评论',     1150, 710),
    'U16': ('评论表情回应',  490, 830),
    # 管理员
    'U17': ('后台登录',      600, 910),
    'U18': ('维护文章',      600, 1000),
    'U19': ('管理评论',      600, 1090),
    'U20': ('管理用户',      600, 1180),
    'U21': ('站点设置',      600, 1270),
    # 微信
    'U22': ('微信问答',     1000, 1180),
}

# edges: (kind, src, dst)  kind: assoc / include / extend / gen / actgen
edges = [
    ('assoc', 'Guest', 'U1'), ('assoc', 'Guest', 'U4'),
    ('assoc', 'Guest', 'U2'), ('assoc', 'Guest', 'U5'),
    ('assoc', 'User', 'U7'), ('assoc', 'User', 'U8'),
    ('assoc', 'User', 'U11'), ('assoc', 'User', 'U13'),
    ('assoc', 'User', 'U14'), ('assoc', 'User', 'U16'),
    ('assoc', 'Admin', 'U17'), ('assoc', 'Admin', 'U18'),
    ('assoc', 'Admin', 'U19'), ('assoc', 'Admin', 'U20'),
    ('assoc', 'Admin', 'U21'),
    ('assoc', 'OAuth', 'U9'), ('assoc', 'Mail', 'U12'),
    ('assoc', 'WeChat', 'U22'),
    ('include', 'U7', 'U12'), ('include', 'U11', 'U12'),
    ('extend', 'U3', 'U2'), ('extend', 'U6', 'U2'),
    ('extend', 'U10', 'U9'),
    ('gen', 'U9', 'U8'), ('gen', 'U15', 'U14'),
    ('actgen', 'User', 'Guest'),
]

# ---------------- 几何 ----------------
def actor_anchor(aid):
    _, x, y = actors[aid]
    return (x + 16, y - 19)   # 右手位置

def ellipse_pt(uc, toward):
    """从用例椭圆中心指向 toward 的边界点"""
    _, cx, cy = ucs[uc]
    rx, ry = ell(_[0])
    dx, dy = toward[0]-cx, toward[1]-cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    nx, ny = dx/rx, dy/ry
    n = math.hypot(nx, ny)
    return (cx + rx*nx/n, cy + ry*ny/n)

def endpoints(kind, src, dst):
    if kind == 'actgen':
        _, x1, y1 = actors[src]; _, x2, y2 = actors[dst]
        return (x1, y1-50), (x2, y2+24)
    if src in actors:
        p1 = actor_anchor(src)
        p2 = ellipse_pt(dst, p1)
    elif dst in actors:
        p2 = actor_anchor(dst)
        p1 = ellipse_pt(src, p2)
    else:
        c1 = ucs[src][1:]; c2 = ucs[dst][1:]
        p1 = ellipse_pt(src, c2); p2 = ellipse_pt(dst, p1)
    return p1, p2

def collision_report():
    """检查每条线段是否穿过任何椭圆，并报告最小间隙"""
    out = []
    for kind, src, dst in edges:
        p1, p2 = endpoints(kind, src, dst)
        worst = []
        for uid, (name, cx, cy) in ucs.items():
            if uid in (src, dst):
                continue
            rx, ry = ell(name)
            mind = None
            for i in range(401):
                t = i/400
                x = p1[0] + (p2[0]-p1[0])*t
                y = p1[1] + (p2[1]-p1[1])*t
                f = ((x-cx)/rx)**2 + ((y-cy)/ry)**2
                d = (math.sqrt(f)-1) * min(rx, ry)
                if mind is None or d < mind:
                    mind = d
            if mind < 12:
                worst.append((round(mind, 1), uid, name))
        worst.sort()
        if worst:
            out.append((f'{kind} {src}->{dst}', worst[:3]))
    return out

# ---------------- SVG ----------------
def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def stick_figure(x, y, name):
    g = []
    g.append(f'<circle cx="{x}" cy="{y-40}" r="11" fill="none" stroke="#111" stroke-width="2"/>')
    g.append(f'<line x1="{x}" y1="{y-29}" x2="{x}" y2="{y+4}" stroke="#111" stroke-width="2"/>')
    g.append(f'<line x1="{x-17}" y1="{y-19}" x2="{x}" y2="{y-25}" stroke="#111" stroke-width="2"/>')
    g.append(f'<line x1="{x}" y1="{y-25}" x2="{x+17}" y2="{y-19}" stroke="#111" stroke-width="2"/>')
    g.append(f'<line x1="{x}" y1="{y+4}" x2="{x-14}" y2="{y+26}" stroke="#111" stroke-width="2"/>')
    g.append(f'<line x1="{x}" y1="{y+4}" x2="{x+14}" y2="{y+26}" stroke="#111" stroke-width="2"/>')
    g.append(f'<text x="{x}" y="{y+52}" font-size="{FONT}" text-anchor="middle" fill="#111">{esc(name)}</text>')
    return g

def usecase(uid):
    name, cx, cy = ucs[uid]
    rx, ry = ell(name)
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{ry}" fill="#fff" stroke="#111" stroke-width="1.8"/>' \
           f'<text x="{cx}" y="{cy+6}" font-size="{FONT}" text-anchor="middle" fill="#111">{esc(name)}</text>'

def arrow_open(p_from, p_to, color='#111'):
    """开放箭头（虚线用）"""
    ang = math.atan2(p_to[1]-p_from[1], p_to[0]-p_from[0])
    a1 = ang + math.radians(155); a2 = ang - math.radians(155)
    L = 14
    q1 = (p_to[0]+L*math.cos(a1), p_to[1]+L*math.sin(a1))
    q2 = (p_to[0]+L*math.cos(a2), p_to[1]+L*math.sin(a2))
    return f'<path d="M {q1[0]:.1f} {q1[1]:.1f} L {p_to[0]:.1f} {p_to[1]:.1f} L {q2[0]:.1f} {q2[1]:.1f}" fill="none" stroke="{color}" stroke-width="1.8"/>'

def arrow_triangle(p_from, p_to, color='#111'):
    """空心三角（继承用）"""
    ang = math.atan2(p_to[1]-p_from[1], p_to[0]-p_from[0])
    L, Wd = 16, 9
    base = (p_to[0]-L*math.cos(ang), p_to[1]-L*math.sin(ang))
    perp = (math.cos(ang+math.pi/2), math.sin(ang+math.pi/2))
    q1 = (base[0]+Wd*perp[0], base[1]+Wd*perp[1])
    q2 = (base[0]-Wd*perp[0], base[1]-Wd*perp[1])
    return f'<path d="M {p_to[0]:.1f} {p_to[1]:.1f} L {q1[0]:.1f} {q1[1]:.1f} L {q2[0]:.1f} {q2[1]:.1f} Z" fill="#fff" stroke="{color}" stroke-width="1.8"/>'

def edge_svg(kind, src, dst):
    p1, p2 = endpoints(kind, src, dst)
    g = []
    if kind == 'assoc':
        g.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="#111" stroke-width="1.8"/>')
    elif kind in ('include', 'extend'):
        g.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="#111" stroke-width="1.8" stroke-dasharray="8,6"/>')
        g.append(arrow_open(p1, p2))
        mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
        label = '包含' if kind == 'include' else '扩展'
        lx, ly = mid[0], mid[1]-14
        lw = tw(label)+12
        g.append(f'<rect x="{lx-lw/2}" y="{ly-16}" width="{lw}" height="22" fill="#fff"/>')
        g.append(f'<text x="{lx}" y="{ly}" font-size="{FONT-2}" text-anchor="middle" fill="#111">{label}</text>')
    elif kind == 'gen':
        g.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="#111" stroke-width="1.8"/>')
        g.append(arrow_triangle(p1, p2))
        mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
        g.append(f'<rect x="{mid[0]-26}" y="{mid[1]-30}" width="52" height="22" fill="#fff"/>')
        g.append(f'<text x="{mid[0]}" y="{mid[1]-14}" font-size="{FONT-2}" text-anchor="middle" fill="#111">继承</text>')
    elif kind == 'actgen':
        g.append(f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="#111" stroke-width="1.8"/>')
        g.append(arrow_triangle(p1, p2))
        g.append(f'<rect x="{p1[0]+8}" y="430" width="52" height="22" fill="#fff"/>')
        g.append(f'<text x="{p1[0]+34}" y="446" font-size="{FONT-2}" text-anchor="middle" fill="#111">继承</text>')
    return g

parts = []
parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')
parts.append(f'<rect x="{BX1}" y="{BY1}" width="{BX2-BX1}" height="{BY2-BY1}" rx="10" fill="none" stroke="#111" stroke-width="2.2"/>')
parts.append(f'<text x="{(BX1+BX2)/2}" y="{BY1+40}" font-size="24" font-weight="bold" text-anchor="middle" fill="#111">知识分享博客系统</text>')

for kind, src, dst in edges:
    parts += edge_svg(kind, src, dst)

for uid in ucs:
    parts.append(usecase(uid))

for aid, (name, x, y) in actors.items():
    parts += stick_figure(x, y, name)

svg = '\n'.join(parts)
html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ margin:0; padding:0; }}
text {{ font-family: "Microsoft YaHei","SimHei",sans-serif; }}
</style></head>
<body><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg}</svg></body></html>'''

open('usecase_ref.html', 'w', encoding='utf-8').write(html)

rep = collision_report()
print("=== 碰撞报告（间隙<12px 的连线）===")
if not rep:
    print("无碰撞，全部连线间隙 >= 12px")
for e, w in rep:
    print(e, '->', w)
