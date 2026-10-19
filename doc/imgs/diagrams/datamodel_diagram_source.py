# -*- coding: utf-8 -*-
"""数据模型 UML 类图生成器：5 个数据包（对应 D1-D5）、15 个实体、关联与多重性。
精确坐标 + 连线避让检测，输出 HTML/SVG，由无头 Chrome 截图。"""
import math

W, H = 1560, 1400
FONT = 16
LINE_H = 20
HEAD_H = 40

def tw(s, fs=FONT):
    return sum(fs if ord(ch) > 0x2e80 else fs * 0.55 for ch in s)

packages = [
    # (x, y, w, h, title)
    (60, 60, 720, 600, '账户与权限数据（D1）'),
    (840, 60, 660, 500, '内容数据（D2）'),
    (840, 620, 660, 460, '评论数据（D3）'),
    (60, 720, 720, 380, '配置数据（D4）'),
    (60, 1160, 720, 180, '日志数据（D5）'),
]

classes = {
    'BlogUser': dict(x=100, y=130, w=250, pkg=0,
        fields=['id : int', 'username : varchar(150)', 'password : varchar(128)', 'email : varchar(254)',
                'is_active : bool', 'is_staff : bool', 'nickname : varchar(100)', 'source : varchar(100)']),
    'OAuthUser': dict(x=420, y=120, w=230, pkg=0,
        fields=['id : int', 'openid : varchar(50)', 'nickname : varchar(50)', 'type : varchar(50)',
                'email : varchar(50)', 'token : varchar(150)']),
    'OAuthConfig': dict(x=420, y=350, w=230, pkg=0,
        fields=['id : int', 'type : varchar(10)', 'appkey : varchar(200)', 'callback_url : varchar(200)',
                'is_enable : bool']),
    'Session': dict(x=100, y=410, w=230, pkg=0,
        fields=['session_key : varchar(40)', 'session_data : text', 'expire_date : datetime']),
    'Article': dict(x=880, y=130, w=260, pkg=1,
        fields=['id : int', 'title : varchar(200)', 'body : longtext', 'pub_time : datetime',
                'status : char(1)', 'comment_status : char(1)', 'views : int']),
    'Category': dict(x=1190, y=130, w=230, pkg=1,
        fields=['id : int', 'name : varchar(30)', 'slug : varchar(60)', 'index : int']),
    'Tag': dict(x=1190, y=310, w=230, pkg=1,
        fields=['id : int', 'name : varchar(30)', 'slug : varchar(60)']),
    'Comment': dict(x=880, y=690, w=270, pkg=2,
        fields=['id : int', 'body : text', 'is_enable : bool', 'creation_time : datetime',
                'parent_comment_id : int']),
    'CommentReaction': dict(x=1190, y=690, w=250, pkg=2,
        fields=['id : int', 'reaction_type : varchar(10)', 'created_at : datetime']),
    'BlogSettings': dict(x=100, y=790, w=280, pkg=3,
        fields=['site_name : varchar(200)', 'article_sub_length : int', 'comment_need_review : bool',
                'color_scheme : varchar(20)']),
    'Links': dict(x=440, y=790, w=230, pkg=3,
        fields=['id : int', 'name : varchar(30)', 'link : varchar(200)', 'sequence : int',
                'is_enable : bool']),
    'SideBar': dict(x=100, y=960, w=230, pkg=3,
        fields=['id : int', 'name : varchar(100)', 'content : text', 'sequence : int']),
    'commands': dict(x=440, y=980, w=230, pkg=3,
        fields=['id : int', 'title : varchar(300)', 'command : varchar(2000)']),
    'EmailSendLog': dict(x=100, y=1195, w=270, pkg=4,
        fields=['id : int', 'emailto : varchar(300)', 'title : varchar(2000)', 'send_result : bool']),
}

def cheight(n):
    return HEAD_H + LINE_H * len(classes[n]['fields']) + 10

for n, c in classes.items():
    c['h'] = cheight(n)

def rect_anchor(n, toward):
    x, y, w, h = n['x'], n['y'], n['w'], n['h']
    cx, cy = x + w/2, y + h/2
    dx, dy = toward[0]-cx, toward[1]-cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    tx = (w/2)/abs(dx) if dx else 1e9
    ty = (h/2)/abs(dy) if dy else 1e9
    t = min(tx, ty)
    return (cx + dx*t, cy + dy*t)

def anchor(alias, toward):
    return rect_anchor(classes[alias], toward)

# 关联: (a, b, 标签, 多重性a, 多重性b, waypoints, 虚线?)
assocs = [
    ('BlogUser', 'OAuthUser', '绑定', '1', '0..*', [], False),
    ('BlogUser', 'Session', '登录会话（逻辑）', '1', '0..*', [], True),
    ('BlogUser', 'Article', '撰写', '1', '0..*', [(320, 100), (810, 100), (810, 150)], False),
    ('BlogUser', 'Comment', '发表', '1', '0..*', [(360, 320), (800, 320), (800, 700)], False),
    ('BlogUser', 'CommentReaction', '回应', '1', '0..*', [(362, 330), (812, 330), (812, 860), (1220, 860), (1220, 798)], False),
    ('Article', 'Category', '归属', '0..*', '1', [], False),
    ('Article', 'Tag', '标注', '0..*', '0..*', [], False),
    ('Article', 'Comment', '所属文章', '1', '0..*', [], False),
    ('Comment', 'Comment', '父评论（回复）', '1', '0..*', [(930, 690), (930, 670), (1010, 670), (1010, 690)], False),
    ('Comment', 'CommentReaction', '针对', '1', '0..*', [], False),
]

def polyline_for(a, b, wps, self_loop=False):
    if self_loop:
        return [(a[0], a[1])] + wps
    if wps:
        p0 = anchor(a, wps[0])
        pn = anchor(b, wps[-1])
        return [p0] + wps + [pn]
    pa = (classes[a]['x'] + classes[a]['w']/2, classes[a]['y'] + classes[a]['h']/2)
    pb = (classes[b]['x'] + classes[b]['w']/2, classes[b]['y'] + classes[b]['h']/2)
    p0 = anchor(a, pb)
    pn = anchor(b, p0)
    return [p0, pn]

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>']

# 包（文件夹形）
for (x, y, w, h, title) in packages:
    parts.append(f'<path d="M {x} {y+22} L {x} {y} L {x+190} {y} L {x+190} {y+22} L {x+w} {y+22} L {x+w} {y+h} L {x} {y+h} Z" fill="none" stroke="#555" stroke-width="1.6"/>')
    parts.append(f'<text x="{x+10}" y="{y+16}" font-size="{FONT}" fill="#111" font-weight="bold">{esc(title)}</text>')

# 关联线
for (a, b, label, ma, mb, wps, dashed) in assocs:
    self_loop = (a == b)
    if self_loop:
        pts = [(930, 690), (930, 670), (1010, 670), (1010, 690)]
    else:
        pts = polyline_for(a, b, wps)
    style = ' stroke-dasharray="7,5"' if dashed else ''
    parts.append(f'<polyline points="{" ".join(f"{px:.1f},{py:.1f}" for px,py in pts)}" fill="none" stroke="#111" stroke-width="1.6"{style}/>')
    # 标签：放在折线中段
    if len(pts) >= 2:
        if self_loop:
            lx, ly = 970, 652
        else:
            # 取中间段中点
            mid = len(pts)//2
            ax, ay = pts[mid-1]; bx, by = pts[mid]
            lx, ly = (ax+bx)/2, (ay+by)/2
            if abs(bx-ax) > abs(by-ay):
                ly -= 14
            else:
                lx += 18
        lw = tw(label, FONT-2) + 10
        parts.append(f'<rect x="{lx-lw/2:.1f}" y="{ly-15:.1f}" width="{lw:.1f}" height="21" fill="#fff"/>')
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="{FONT-2}" text-anchor="middle" fill="#111">{esc(label)}</text>')
    # 多重性
    if self_loop:
        mpos = [(940, 684, '0..*'), (1000, 684, '1')]
        for mx, my, txt in mpos:
            parts.append(f'<text x="{mx}" y="{my}" font-size="{FONT-3}" text-anchor="middle" fill="#111">{txt}</text>')
    else:
        p0, p1 = pts[0], pts[1]
        pn2, pn1 = pts[-1], pts[-2]
        def mpos(p, q, txt, offset_sign):
            dx, dy = q[0]-p[0], q[1]-p[1]
            m = math.hypot(dx, dy) or 1
            nx, ny = -dy/m, dx/m
            return (p[0] + nx*16*offset_sign + (8 if abs(dx) > abs(dy) else 0),
                    p[1] + ny*16*offset_sign - (12 if abs(dx) > abs(dy) else 0), txt)
        for mx, my, txt in [mpos(p0, p1, ma, 1), mpos(pn2, pn1, mb, -1)]:
            parts.append(f'<text x="{mx:.1f}" y="{my:.1f}" font-size="{FONT-3}" text-anchor="middle" fill="#111">{txt}</text>')

# 类框
for name, c in classes.items():
    x, y, w, h = c['x'], c['y'], c['w'], c['h']
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#111" stroke-width="1.8"/>')
    parts.append(f'<line x1="{x}" y1="{y+HEAD_H}" x2="{x+w}" y2="{y+HEAD_H}" stroke="#111" stroke-width="1.4"/>')
    parts.append(f'<text x="{x+w/2}" y="{y+26}" font-size="{FONT}" font-weight="bold" text-anchor="middle" fill="#111">{esc(name)}</text>')
    for i, f in enumerate(c['fields']):
        parts.append(f'<text x="{x+12}" y="{y+HEAD_H+20+i*LINE_H}" font-size="{FONT-2}" fill="#111">{esc(f)}</text>')

svg = '\n'.join(parts)
html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:0}} text{{font-family:"Microsoft YaHei","SimHei",sans-serif}}
</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg}</svg></body></html>'''
open('datamodel.html', 'w', encoding='utf-8').write(html)

# 简单碰撞检查：关联线是否穿过非端点类框
def seg_rect_pts(pts, box):
    x, y, w, h = box
    for i in range(len(pts)-1):
        ax, ay = pts[i]; bx, by = pts[i+1]
        for k in range(81):
            t = k/80
            px, py = ax+(bx-ax)*t, ay+(by-ay)*t
            if x-1 <= px <= x+w+1 and y-1 <= py <= y+h+1:
                return True
    return False

print('=== 碰撞检查 ===')
issues = 0
for a, b, label, ma, mb, wps, dashed in assocs:
    if a == b:
        continue
    pts = polyline_for(a, b, wps)
    for name, c in classes.items():
        if name in (a, b):
            continue
        if seg_rect_pts(pts, (c['x'], c['y'], c['w'], c['h'])):
            print(f'  关联 {a}-{b}（{label}）穿过类框 {name}')
            issues += 1
if not issues:
    print('  无穿框')
print('OK datamodel.html')
