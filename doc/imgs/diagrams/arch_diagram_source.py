# -*- coding: utf-8 -*-
"""系统架构图（UML 包图，分层）：界面层 / 应用层 / 领域模型层 / 基础设施层。
仿模板参考样式：浅色层带 + 文件夹形包 + 虚线 «use» 依赖。"""
import math

W, H = 1900, 1240
FONT = 16

def tw(s, fs=FONT):
    return sum(fs if ord(ch) > 0x2e80 else fs * 0.55 for ch in s)

bands = [
    dict(y=70, h=230, title='界面层', fill='#FFF7E8', tab='#F2C97D'),
    dict(y=340, h=300, title='应用层', fill='#EEF4FF', tab='#9DB9E8'),
    dict(y=680, h=300, title='领域模型层', fill='#FDECEC', tab='#E9A6A6'),
    dict(y=1020, h=160, title='基础设施层', fill='#F3ECFF', tab='#B9A0E8'),
]

# (band, x, y, w, h, title, [subtitle lines])
pkgs = [
    # 界面层
    (0, 140, 150, 460, 110, '页面模板 templates', ['base.html / base_account.html', '博客、账户、搜索与错误页模板']),
    (0, 640, 150, 460, 110, '模板标签 templatetags', ['blog_tags / comments_tags / oauth_tags', '包含标签渲染页面片段']),
    (0, 1140, 150, 460, 110, '前端资源 frontend', ['Vite + Alpine.js + HTMX + Tailwind CSS', '明暗主题、响应式与交互']),
    # 应用层
    (1, 140, 420, 250, 170, 'blog 内容与搜索', ['IndexView / ArticleDetailView', 'Category / Tag / ArchivesView', 'EsSearchView（Haystack）']),
    (1, 420, 420, 250, 170, 'accounts 账户', ['RegisterView / LoginView', 'LogoutView / ForgetPasswordView', '账户表单与结果页']),
    (1, 700, 420, 250, 170, 'comments 评论', ['CommentPostView', 'CommentReactionView', '评论通知与表情回应']),
    (1, 980, 420, 250, 170, 'oauth 第三方登录', ['authorize / oauthlogin', 'RequireEmailView / bindsuccess', '第三方账号绑定']),
    (1, 1260, 420, 250, 170, 'servermanager 微信与运维', ['WeRoBot 公众号机器人', 'EmailSendLog / commands', '邮件与运维接口']),
    (1, 1540, 420, 250, 170, 'djangoblog 公共支撑', ['base_views / mixins / middleware', 'plugin_manage / admin_site', 'settings / utils / signals']),
    # 领域模型层
    (2, 140, 760, 250, 170, '内容模型', ['Article / Category / Tag', '搜索索引 documents', '文章状态与评论开关']),
    (2, 420, 760, 250, 170, '账户模型', ['BlogUser', '（扩展 Django AbstractUser）', '昵称、来源、激活状态']),
    (2, 700, 760, 250, 170, '评论模型', ['Comment / CommentReaction', '嵌套评论（自关联）', '表情唯一约束']),
    (2, 980, 760, 250, 170, '第三方账号模型', ['OAuthUser / OAuthConfig', 'openid 与平台配置', '绑定关系']),
    (2, 1260, 760, 250, 170, '运维模型', ['EmailSendLog / commands', '邮件日志与命令定义', '操作日志（内置表）']),
    (2, 1540, 760, 250, 170, '插件体系 plugins', ['阅读时间 / 版权 / 推荐', '图片懒加载 / SEO', '浏览量统计']),
    # 基础设施层
    (3, 140, 1080, 250, 80, 'MySQL 数据库', ['业务数据持久化']),
    (3, 420, 1080, 250, 80, 'Redis 缓存/会话', ['页面缓存、侧栏缓存']),
    (3, 700, 1080, 250, 80, '搜索服务', ['Whoosh / Elasticsearch']),
    (3, 980, 1080, 250, 80, 'SMTP 邮件服务', ['激活/验证码/通知邮件']),
    (3, 1260, 1080, 250, 80, '微信平台', ['公众号消息中转']),
    (3, 1540, 1080, 250, 80, '静态/媒体文件', ['static、media 存储']),
]

# (x1,y1,x2,y2,label)
arrows = [
    (265, 260, 265, 420, '«use»'),
    (870, 260, 870, 420, '«use»'),
    (1380, 260, 1380, 420, '«use»'),
    (265, 590, 265, 760, '«use»'),
    (825, 590, 825, 760, '«use»'),
    (1385, 590, 1385, 760, '«use»'),
    (1665, 590, 1665, 760, '«加载/扩展»'),
    (265, 930, 265, 1080, '«use»'),
    (545, 930, 545, 1080, '«use»'),
    (1300, 930, 1300, 1080, '«use»'),
]
# 右侧绕行：应用层直接使用基础设施（缓存/邮件/搜索）
bypass = [(1790, 540), (1850, 540), (1850, 1120), (1790, 1120)]

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

parts = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>']

# 层带
for b in bands:
    parts.append(f'<rect x="80" y="{b["y"]}" width="1740" height="{b["h"]}" rx="6" fill="{b["fill"]}" stroke="#888" stroke-width="1.2"/>')
    parts.append(f'<rect x="80" y="{b["y"]+10}" width="150" height="30" rx="4" fill="{b["tab"]}" stroke="#666" stroke-width="1"/>')
    parts.append(f'<text x="155" y="{b["y"]+31}" font-size="{FONT}" font-weight="bold" text-anchor="middle" fill="#111">{esc(b["title"])}</text>')

# 包（文件夹形）
for (bi, x, y, w, h, title, subs) in pkgs:
    tabw = 120
    parts.append(f'<path d="M {x} {y+22} L {x} {y} L {x+tabw} {y} L {x+tabw} {y+22} L {x+w} {y+22} L {x+w} {y+h} L {x} {y+h} Z" fill="#fff" stroke="#111" stroke-width="1.6"/>')
    parts.append(f'<text x="{x+w/2}" y="{y+22+28}" font-size="{FONT}" font-weight="bold" text-anchor="middle" fill="#111">{esc(title)}</text>')
    for i, s in enumerate(subs):
        parts.append(f'<text x="{x+w/2}" y="{y+22+54+i*22}" font-size="{FONT-2}" text-anchor="middle" fill="#222">{esc(s)}</text>')

def arrow_head(x1, y1, x2, y2):
    ang = math.atan2(y2-y1, x2-x1)
    L = 13
    a1 = ang + math.radians(155); a2 = ang - math.radians(155)
    q1 = (x2 + L*math.cos(a1), y2 + L*math.sin(a1))
    q2 = (x2 + L*math.cos(a2), y2 + L*math.sin(a2))
    return f'<path d="M {q1[0]:.1f} {q1[1]:.1f} L {x2:.1f} {y2:.1f} L {q2[0]:.1f} {q2[1]:.1f}" fill="none" stroke="#111" stroke-width="1.8"/>'

def label(x, y, text):
    w = tw(text, FONT-2) + 12
    return (f'<rect x="{x-w/2:.1f}" y="{y-15:.1f}" width="{w:.1f}" height="21" fill="#fff"/>'
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{FONT-2}" text-anchor="middle" fill="#111">{esc(text)}</text>')

for (x1, y1, x2, y2, text) in arrows:
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#111" stroke-width="1.7" stroke-dasharray="8,6"/>')
    parts.append(arrow_head(x1, y1, x2, y2))
    parts.append(label(x1, (y1+y2)/2 - 4, text))

# 右侧绕行
pts = ' '.join(f'{x},{y}' for x, y in bypass)
parts.append(f'<polyline points="{pts}" fill="none" stroke="#111" stroke-width="1.7" stroke-dasharray="8,6"/>')
parts.append(arrow_head(bypass[-2][0], bypass[-2][1], bypass[-1][0], bypass[-1][1]))
parts.append(label(1850, 760, '«use»'))

svg = '\n'.join(parts)
html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;padding:0}} text{{font-family:"Microsoft YaHei","SimHei",sans-serif}}
</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg}</svg></body></html>'''
open('arch.html', 'w', encoding='utf-8').write(html)
print('OK arch.html')
