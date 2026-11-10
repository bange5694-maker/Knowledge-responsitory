# -*- coding: utf-8 -*-
"""知识分享博客系统 数据流图（DFD）生成器：顶层图 / 0 层图 / P3、P2 的 1 层图。
图形约定：外部实体=矩形，加工=椭圆（编号+名称），数据存储=左封闭右开口的平行线框，
数据流=带箭头折线+标注。输出 HTML（SVG），由无头 Chrome 截图。"""
import math

FONT = 17

def tw(s, fs=FONT):
    w = 0
    for ch in s:
        w += fs if ord(ch) > 0x2e80 else fs * 0.55
    return w

class Node:
    def __init__(self, kind, label, x, y, w=None, h=None, rx=None, ry=None):
        self.kind, self.label, self.x, self.y = kind, label, x, y
        self.w, self.h, self.rx, self.ry = w, h, rx, ry

def rect_anchor(n, toward):
    hw, hh = n.w / 2, n.h / 2
    dx, dy = toward[0] - n.x, toward[1] - n.y
    if dx == 0 and dy == 0:
        return (n.x, n.y)
    tx = hw / abs(dx) if dx else 1e9
    ty = hh / abs(dy) if dy else 1e9
    t = min(tx, ty)
    return (n.x + dx * t, n.y + dy * t)

def ellipse_anchor(n, toward):
    dx, dy = toward[0] - n.x, toward[1] - n.y
    if dx == 0 and dy == 0:
        return (n.x, n.y)
    nx, ny = dx / n.rx, dy / n.ry
    m = math.hypot(nx, ny)
    return (n.x + n.rx * nx / m, n.y + n.ry * ny / m)

def anchor(n, toward):
    return ellipse_anchor(n, toward) if n.kind == 'process' else rect_anchor(n, toward)

class Flow:
    def __init__(self, src, dst, label, frac=0.5, off=16.0, shift=0.0, waypoints=None, ldx=None, ldy=None):
        self.src, self.dst, self.label = src, dst, label
        self.frac, self.off, self.shift = frac, off, shift
        self.waypoints = waypoints or []
        self.ldx, self.ldy = ldx, ldy

def polyline(nodes, f):
    src, dst = nodes[f.src], nodes[f.dst]
    mids = [tuple(p) for p in f.waypoints]
    seq = [None] + mids + [None]
    # 起点朝向第一个中继点（或终点中心）
    tgt1 = mids[0] if mids else (dst.x, dst.y)
    p0 = anchor(src, tgt1)
    tgt2 = mids[-1] if mids else (src.x, src.y)
    pn = anchor(dst, tgt2)
    pts = [p0] + mids + [pn]
    if f.shift:
        # 整体沿第一段/最后一段的垂直方向平移
        ax, ay = pts[0]; bx, by = pts[1]
        dx, dy = bx - ax, by - ay
        m = math.hypot(dx, dy) or 1
        ox, oy = -dy / m * f.shift, dx / m * f.shift
        pts = [(x + ox, y + oy) for x, y in pts]
    return pts

def point_at(pts, frac):
    segs = []
    total = 0.0
    for i in range(len(pts) - 1):
        L = math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1])
        segs.append((L, i)); total += L
    target = total * frac
    acc = 0.0
    for L, i in segs:
        if acc + L >= target:
            t = (target - acc) / L if L else 0
            ax, ay = pts[i]; bx, by = pts[i+1]
            return (ax + (bx-ax)*t, ay + (by-ay)*t, i)
        acc += L
    return (pts[-1][0], pts[-1][1], len(pts)-2)

def label_pos(pts, f):
    x, y, i = point_at(pts, f.frac)
    if f.ldx is not None:
        return (x + f.ldx, y + f.ldy)
    ax, ay = pts[i]; bx, by = pts[i+1]
    dx, dy = bx-ax, by-ay
    m = math.hypot(dx, dy) or 1
    return (x - dy/m*f.off, y + dx/m*f.off)

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def draw_node(n):
    g = []
    if n.kind == 'entity':
        g.append(f'<rect x="{n.x-n.w/2}" y="{n.y-n.h/2}" width="{n.w}" height="{n.h}" fill="#fff" stroke="#111" stroke-width="2"/>')
        for i, line in enumerate(n.label):
            g.append(f'<text x="{n.x}" y="{n.y - (len(n.label)-1)*11 + i*22 + 6}" font-size="{FONT}" text-anchor="middle" fill="#111">{esc(line)}</text>')
    elif n.kind == 'process':
        g.append(f'<ellipse cx="{n.x}" cy="{n.y}" rx="{n.rx}" ry="{n.ry}" fill="#fff" stroke="#111" stroke-width="2"/>')
        nlines = len(n.label)
        for i, line in enumerate(n.label):
            size = FONT if i == 0 else FONT - 1
            g.append(f'<text x="{n.x}" y="{n.y - (nlines-1)*11 + i*22 + 6}" font-size="{size}" font-weight="{"bold" if i==0 else "normal"}" text-anchor="middle" fill="#111">{esc(line)}</text>')
    elif n.kind == 'store':
        x1, y1 = n.x - n.w/2, n.y - n.h/2
        x2, y2 = n.x + n.w/2, n.y + n.h/2
        g.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y1}" stroke="#111" stroke-width="2"/>')
        g.append(f'<line x1="{x1}" y1="{y2}" x2="{x2}" y2="{y2}" stroke="#111" stroke-width="2"/>')
        g.append(f'<line x1="{x1}" y1="{y1}" x2="{x1}" y2="{y2}" stroke="#111" stroke-width="2"/>')
        for i, line in enumerate(n.label):
            weight = 'bold' if i == 0 else 'normal'
            g.append(f'<text x="{x1+14}" y="{n.y - (len(n.label)-1)*11 + i*22 + 6}" font-size="{FONT-1}" font-weight="{weight}" fill="#111">{esc(line)}</text>')
    return g

def draw_flow(nodes, f):
    pts = polyline(nodes, f)
    g = [f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" fill="none" stroke="#111" stroke-width="1.7"/>']
    # 箭头
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2-y1, x2-x1)
    L, Wd = 14, 7
    bx, by = x2 - L*math.cos(ang), y2 - L*math.sin(ang)
    px, py = math.cos(ang+math.pi/2), math.sin(ang+math.pi/2)
    q1 = (bx + Wd*px, by + Wd*py); q2 = (bx - Wd*px, by - Wd*py)
    g.append(f'<path d="M {x2:.1f} {y2:.1f} L {q1[0]:.1f} {q1[1]:.1f} L {q2[0]:.1f} {q2[1]:.1f} Z" fill="#111" stroke="none"/>')
    if f.label:
        lx, ly = label_pos(pts, f)
        w = tw(f.label, FONT-2) + 12
        g.append(f'<rect x="{lx-w/2:.1f}" y="{ly-16:.1f}" width="{w:.1f}" height="23" fill="#fff"/>')
        g.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="{FONT-2}" text-anchor="middle" fill="#111">{esc(f.label)}</text>')
    return g

def collision_report(nodes, flows):
    issues = []
    for f in flows:
        pts = polyline(nodes, f)
        worst = []
        for nid, n in nodes.items():
            if nid in (f.src, f.dst):
                continue
            mind = None
            for i in range(len(pts)-1):
                ax, ay = pts[i]; bx, by = pts[i+1]
                for k in range(61):
                    t = k/60
                    x, y = ax + (bx-ax)*t, ay + (by-ay)*t
                    if n.kind == 'process':
                        d = (math.hypot((x-n.x)/n.rx, (y-n.y)/n.ry) - 1) * min(n.rx, n.ry)
                    else:
                        d = max(abs(x-n.x) - n.w/2, abs(y-n.y) - n.h/2)
                    mind = d if mind is None else min(mind, d)
            if mind is not None and mind < 10:
                worst.append((round(mind, 1), nid))
        if worst:
            worst.sort()
            issues.append((f'{f.src}->{f.dst} 「{f.label}」', worst[:3]))
    return issues

def render(title, W, H, nodes, flows, out):
    parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>']
    for f in flows:
        parts += draw_flow(nodes, f)
    for n in nodes.values():
        parts += draw_node(n)
    svg = '\n'.join(parts)
    html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:0}} text{{font-family:"Microsoft YaHei","SimHei",sans-serif}}
</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg}</svg></body></html>'''
    open(out, 'w', encoding='utf-8').write(html)
    rep = collision_report(nodes, flows)
    print(f'--- {title} ---')
    if not rep:
        print('  无碰撞（间隙 >= 10px）')
    for e, w in rep:
        print(' ', e, '->', w)

# =========================================================
# 顶层图
# =========================================================
C = {
    'E1': Node('entity', ['访客'], 170, 180, 170, 60),
    'E2': Node('entity', ['注册用户'], 170, 450, 170, 60),
    'E3': Node('entity', ['管理员'], 170, 720, 170, 60),
    'E4': Node('entity', ['第三方登录平台'], 1330, 180, 190, 60),
    'E5': Node('entity', ['邮件服务器'], 1330, 450, 170, 60),
    'E6': Node('entity', ['微信服务器'], 1330, 720, 170, 60),
    'S0': Node('process', ['0', '知识分享博客系统'], 750, 450, rx=190, ry=100),
}
Cf = [
    Flow('E1', 'S0', '浏览/搜索请求', 0.5, ldx=-10, ldy=-34, shift=-10),
    Flow('S0', 'E1', '页面内容', 0.5, ldx=10, ldy=34, shift=10),
    Flow('E2', 'S0', '注册/登录/评论请求', 0.5, ldx=0, ldy=-34, shift=-10),
    Flow('S0', 'E2', '操作结果/页面', 0.5, ldx=0, ldy=34, shift=10),
    Flow('E3', 'S0', '后台管理请求', 0.5, ldx=-10, ldy=-34, shift=-10),
    Flow('S0', 'E3', '管理结果', 0.5, ldx=10, ldy=34, shift=10),
    Flow('S0', 'E4', '授权请求', 0.5, ldx=-10, ldy=-34, shift=-10),
    Flow('E4', 'S0', '授权信息', 0.5, ldx=10, ldy=34, shift=10),
    Flow('S0', 'E5', '邮件发送请求', 0.5, ldx=0, ldy=-34, shift=-10),
    Flow('E5', 'S0', '投递结果', 0.5, ldx=0, ldy=34, shift=10),
    Flow('E6', 'S0', '微信消息', 0.5, ldx=-10, ldy=-34, shift=-10),
    Flow('S0', 'E6', '自动回复', 0.5, ldx=10, ldy=34, shift=10),
]
render('顶层图', 1500, 900, C, Cf, 'dfd_context.html')

# =========================================================
# 0 层图（实体—加工—存储 三横带，v2）
# =========================================================
Z = {
    'E1': Node('entity', ['访客'], 300, 120, 170, 60),
    'E2': Node('entity', ['注册用户'], 650, 120, 170, 60),
    'E4': Node('entity', ['第三方登录平台'], 1000, 120, 190, 60),
    'E5': Node('entity', ['邮件服务器'], 1350, 120, 170, 60),
    'E3': Node('entity', ['管理员'], 1700, 120, 170, 60),
    'E6': Node('entity', ['微信服务器'], 2000, 120, 170, 60),
    'P2': Node('process', ['P2', '内容浏览与搜索'], 300, 430, rx=115, ry=58),
    'P1': Node('process', ['P1', '用户与权限', '管理'], 650, 430, rx=112, ry=58),
    'P3': Node('process', ['P3', '评论互动'], 1000, 430, rx=105, ry=55),
    'P5': Node('process', ['P5', '通知服务'], 1350, 430, rx=105, ry=55),
    'P4': Node('process', ['P4', '后台管理'], 1700, 430, rx=105, ry=55),
    'P6': Node('process', ['P6', '微信问答'], 2000, 430, rx=105, ry=55),
    'D1': Node('store', ['D1 用户与第三方账号', '（含 OAuth 配置）'], 400, 800, 280, 66),
    'D2': Node('store', ['D2 内容数据', '（文章/分类/标签/索引）'], 800, 800, 300, 66),
    'D3': Node('store', ['D3 评论与表情'], 1200, 800, 250, 66),
    'D4': Node('store', ['D4 站点配置', '（设置/友链/侧边栏）'], 1600, 800, 290, 66),
    'D5': Node('store', ['D5 日志', '（邮件/操作日志）'], 2000, 800, 260, 66),
}
Zf = [
    # 实体—加工（成对，shift 错开）
    Flow('E1', 'P2', '浏览/搜索请求', 0.42, -16, -9),
    Flow('P2', 'E1', '页面内容', 0.42, 16, 9),
    Flow('E2', 'P1', '注册/登录请求', 0.42, -16, -9),
    Flow('P1', 'E2', '登录结果/会话', 0.42, 16, 9),
    Flow('E2', 'P3', '评论/表情请求', 0.30, -22, -8),
    Flow('P3', 'E2', '操作结果', 0.34, 22, 8),
    Flow('E3', 'P4', '管理操作', 0.42, -16, -9),
    Flow('P4', 'E3', '管理结果', 0.42, 16, 9),
    Flow('E4', 'P1', '授权信息', 0.32, -22, 0),
    Flow('P1', 'E4', '授权请求', 0.30, 22, 0),
    Flow('E5', 'P5', '投递结果', 0.42, -16, -9),
    Flow('P5', 'E5', '邮件发送请求', 0.42, 16, 9),
    Flow('E6', 'P6', '微信消息', 0.42, -16, -9),
    Flow('P6', 'E6', '自动回复', 0.42, 16, 9),
    # 加工—存储（标签放中段，缩短）
    Flow('P1', 'D1', '账号数据', 0.55, 16, 0),
    Flow('P2', 'D2', '内容读取', 0.55, 16, 0),
    Flow('P2', 'D3', '评论读取', 0.60, 16, 0),
    Flow('P2', 'D4', '设置/友链', 0.55, ldx=-42, ldy=-4),
    Flow('P3', 'D1', '用户信息', 0.55, 16, 0),
    Flow('P3', 'D2', '评论开关', 0.60, 16, 0),
    Flow('P3', 'D3', '评论/表情', 0.52, ldx=42, ldy=-4),
    Flow('P3', 'D4', '审核设置', 0.62, 16, 0),
    Flow('P4', 'D1', '用户维护', 0.62, 16, 0),
    Flow('P4', 'D2', '内容维护', 0.64, 16, 0),
    Flow('P4', 'D3', '评论维护', 0.66, 16, 0),
    Flow('P4', 'D4', '配置维护', 0.68, 16, 0),
    Flow('P4', 'D5', '操作日志', 0.70, 16, 0),
    Flow('P5', 'D5', '邮件日志', 0.55, 16, 0),
    Flow('P6', 'D2', '文章检索', 0.55, 16, 0),
    # 加工—加工（P1→P5 绕行，P3→P5 相邻）
    Flow('P1', 'P5', '验证/激活邮件请求', 0.72, -16, 0, [(760, 330), (1300, 330)]),
    Flow('P3', 'P5', '评论通知请求', 0.5, -18, 0),
]
render('0 层图', 2200, 940, Z, Zf, 'dfd_level0.html')

# =========================================================
# 1 层图：P3 评论互动
# =========================================================
A = {
    'E2': Node('entity', ['注册用户'], 150, 450, 170, 60),
    'S1': Node('process', ['3.1', '校验评论权限'], 520, 300, rx=120, ry=58),
    'S2': Node('process', ['3.2', '保存评论'], 860, 450, rx=110, ry=58),
    'S3': Node('process', ['3.3', '评论通知'], 1150, 280, rx=110, ry=58),
    'S4': Node('process', ['3.4', '表情回应'], 900, 720, rx=110, ry=58),
    'P5': Node('process', ['P5', '通知服务'], 1380, 450, rx=105, ry=52),
    'D1': Node('store', ['D1 用户与第三方账号', '（含 OAuth 配置）'], 400, 640, 290, 66),
    'D2': Node('store', ['D2 内容数据', '（文章）'], 260, 140, 250, 66),
    'D3': Node('store', ['D3 评论与表情'], 1200, 620, 250, 66),
    'D4': Node('store', ['D4 站点配置'], 760, 140, 230, 66),
}
Af = [
    Flow('E2', 'S1', '评论请求', 0.45, -16, 0),
    Flow('S1', 'D1', '查询用户', 0.55, ldx=-36, ldy=0),
    Flow('D1', 'S1', '用户信息', 0.55, ldx=36, ldy=0),
    Flow('S1', 'D2', '查询文章', 0.38, ldx=-58, ldy=-6),
    Flow('D2', 'S1', '文章/评论开关', 0.62, ldx=58, ldy=-6),
    Flow('S1', 'D4', '读取审核设置', 0.40, ldx=-62, ldy=-8),
    Flow('D4', 'S1', '审核标志', 0.60, ldx=62, ldy=-8),
    Flow('S1', 'S2', '校验通过的评论数据', 0.5, -16, 0),
    Flow('S2', 'D3', '写入评论', 0.6, ldx=-34, ldy=-4),
    Flow('S2', 'S3', '新评论/回复信息', 0.5, -16, 0),
    Flow('S3', 'P5', '通知请求', 0.5, -16, 0),
    Flow('E2', 'S4', '表情请求', 0.55, -16, 0),
    Flow('S4', 'D3', '写入/删除表情', 0.6, ldx=34, ldy=4),
]
render('P3 1 层图', 1500, 850, A, Af, 'dfd_p3.html')

# =========================================================
# 1 层图：P2 内容浏览与搜索
# =========================================================
B = {
    'E1': Node('entity', ['访客'], 150, 450, 170, 60),
    'B1': Node('process', ['2.1', '列表展示'], 520, 220, rx=105, ry=55),
    'B2': Node('process', ['2.2', '文章详情展示'], 520, 680, rx=120, ry=55),
    'B3': Node('process', ['2.3', '搜索'], 900, 220, rx=95, ry=55),
    'B4': Node('process', ['2.4', '友情链接展示'], 900, 680, rx=120, ry=55),
    'D1': Node('store', ['D2', '内容数据（文章/分类/标签）'], 750, 450, 320, 58),
    'D3': Node('store', ['D3', '评论与表情'], 1150, 560, 250, 58),
    'D4': Node('store', ['D4', '站点配置（友链）'], 1150, 320, 260, 58),
}
Bf = [
    Flow('E1', 'B1', '浏览请求', 0.5, shift=-8, ldx=-10, ldy=-34),
    Flow('B1', 'E1', '文章列表', 0.5, shift=8, ldx=10, ldy=34),
    Flow('E1', 'B2', '详情请求', 0.5, shift=-8, ldx=-10, ldy=-34),
    Flow('B2', 'E1', '文章详情', 0.5, shift=8, ldx=10, ldy=34),
    Flow('E1', 'B3', '搜索请求', 0.5, shift=-8, ldx=-10, ldy=-32),
    Flow('B3', 'E1', '搜索结果', 0.5, shift=8, ldx=10, ldy=32),
    Flow('E1', 'B4', '友链请求', 0.5, shift=-8, ldx=-10, ldy=-34),
    Flow('B4', 'E1', '友链列表', 0.5, shift=8, ldx=10, ldy=34),
    Flow('B1', 'D1', '文章/分类/标签', 0.55, 16, 0),
    Flow('B2', 'D1', '文章内容', 0.5, shift=-8, ldx=-10, ldy=-30),
    Flow('B2', 'D3', '评论列表', 0.6, ldx=34, ldy=14),
    Flow('B2', 'D1', '浏览量更新', 0.55, shift=8, ldx=20, ldy=30),
    Flow('B3', 'D1', '索引检索', 0.55, 16, 0),
    Flow('B4', 'D4', '友链数据', 0.55, 16, 0),
]
render('P2 1 层图', 1500, 900, B, Bf, 'dfd_p2.html')
