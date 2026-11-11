# HJJ: Vite资源加载Django模板标签模块
# 用于在Django模板中加载Vite构建的前端资源，支持开发模式(HMR热更新)和生产模式(静态文件)
#
# 使用方法：
#     {% load vite_tags %}
#     {% vite_js 'src/main.js' %}
#     {% vite_css 'src/styles/main.css' %}

import json
import os
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.templatetags.static import static
import logging

register = template.Library()
logger = logging.getLogger(__name__)

# HJJ: 全局缓存manifest内容，生产模式下避免重复读取文件
_manifest_cache = None


def load_manifest():
    """
    HJJ: 加载Vite构建产物manifest.json文件
    该文件包含所有构建资源的映射关系（入口文件 -> 实际输出文件）
    
    返回:
        dict - manifest内容，若文件不存在则返回空字典
    """
    global _manifest_cache

    # HJJ: 开发模式不缓存，每次重新读取；生产模式使用缓存提高性能
    if not settings.DEBUG and _manifest_cache is not None:
        return _manifest_cache

    # HJJ: manifest文件路径（相对于项目根目录）
    manifest_path = os.path.join(
        settings.BASE_DIR,
        'blog/static/blog/dist/.vite/manifest.json'
    )

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            # HJJ: 仅在生产模式下缓存
            if not settings.DEBUG:
                _manifest_cache = manifest
            logger.info(f'✅ Vite manifest loaded from: {manifest_path}')
            return manifest
    except FileNotFoundError:
        # HJJ: 开发模式下manifest可能不存在（Vite开发服务器无需构建）
        logger.warning(f'⚠️  Vite manifest not found: {manifest_path}')
        logger.warning('🔧 Running in development mode. Make sure Vite dev server is running.')
        return {}
    except json.JSONDecodeError as e:
        logger.error(f'❌ Failed to parse manifest.json: {e}')
        return {}


@register.simple_tag
def vite_asset(entry_name):
    """
    HJJ: 获取Vite构建资源的URL
    
    参数:
        entry_name: str - 入口文件名，如 'src/main.js'
    返回:
        str - 资源URL（生产模式指向构建文件，开发模式指向Vite开发服务器）
    
    用法:
        {% vite_asset 'src/main.js' %}
    """
    manifest = load_manifest()

    if entry_name in manifest:
        file_path = manifest[entry_name]['file']
        return static(f'blog/dist/{file_path}')

    # HJJ: 开发模式回退到Vite开发服务器
    vite_dev_server = getattr(settings, 'VITE_DEV_SERVER_URL', 'http://localhost:5173')
    return f'{vite_dev_server}/{entry_name}'


@register.simple_tag
def vite_js(entry_name='src/main.js'):
    """
    HJJ: 加载Vite构建的JavaScript资源
    
    开发模式：加载Vite开发服务器的资源（带HMR热更新）
    生产模式：加载构建后的静态文件
    
    参数:
        entry_name: str - JS入口文件名，默认 'src/main.js'
    返回:
        SafeString - HTML script/link标签
    
    用法:
        {% vite_js 'src/main.js' %}
    """
    manifest = load_manifest()

    # HJJ: 开发模式：使用Vite开发服务器
    if not manifest:
        vite_dev_server = getattr(settings, 'VITE_DEV_SERVER_URL', 'http://localhost:5173')
        return mark_safe(f'''
            <!-- Vite开发模式 -->
            <script type="module" src="{vite_dev_server}/@vite/client"></script>
            <script type="module" src="{vite_dev_server}/{entry_name}"></script>
        ''')

    # HJJ: 生产模式：使用构建后的文件
    if entry_name not in manifest:
        logger.error(f'❌ Entry "{entry_name}" not found in manifest')
        return ''

    entry_data = manifest[entry_name]
    file_path = entry_data['file']
    js_url = static(f'blog/dist/{file_path}')

    # HJJ: 收集该入口关联的所有CSS文件（Vite代码分割产生的CSS）
    css_html = ''
    if 'css' in entry_data:
        for css_file in entry_data['css']:
            css_url = static(f'blog/dist/{css_file}')
            css_html += f'    <link rel="stylesheet" href="{css_url}">\n'

    return mark_safe(f'''
    <!-- Vite生产模式 -->
{css_html}    <script type="module" crossorigin src="{js_url}"></script>
''')


@register.simple_tag
def vite_css(entry_name='src/styles/main.css'):
    """
    HJJ: 加载Vite构建的CSS资源
    
    注意：开发模式下CSS通过JS注入，不需要单独加载link标签
    
    参数:
        entry_name: str - CSS入口文件名，默认 'src/styles/main.css'
    返回:
        SafeString - HTML link标签（开发模式返回空字符串）
    
    用法:
        {% vite_css 'src/styles/main.css' %}
    """
    manifest = load_manifest()

    # HJJ: 开发模式：CSS通过Vite的HMR自动注入，无需手动加载
    if not manifest:
        return ''

    # HJJ: 生产模式：加载构建后的CSS
    if entry_name not in manifest:
        logger.error(f'❌ Entry "{entry_name}" not found in manifest')
        return ''

    file_path = manifest[entry_name]['file']
    css_url = static(f'blog/dist/{file_path}')
    return mark_safe(f'<link rel="stylesheet" href="{css_url}">')


@register.simple_tag
def vite_preload(entry_name):
    """
    HJJ: 预加载Vite资源，优化关键资源的加载速度
    
    参数:
        entry_name: str - 入口文件名
    返回:
        SafeString - HTML preload标签
    
    用法:
        {% vite_preload 'src/main.js' %}
    """
    manifest = load_manifest()

    if not manifest or entry_name not in manifest:
        return ''

    file_path = manifest[entry_name]['file']
    url = static(f'blog/dist/{file_path}')

    # HJJ: 根据文件类型选择合适的预加载方式
    if file_path.endswith('.js'):
        return mark_safe(f'<link rel="modulepreload" crossorigin href="{url}">')
    elif file_path.endswith('.css'):
        return mark_safe(f'<link rel="preload" href="{url}" as="style">')
    else:
        return mark_safe(f'<link rel="preload" href="{url}">')


@register.simple_tag
def is_vite_dev_mode():
    """
    HJJ: 判断当前是否处于Vite开发模式
    
    返回:
        bool - 开发模式返回True，生产模式返回False
    
    用法:
        {% is_vite_dev_mode as dev_mode %}
        {% if dev_mode %}
            <div class="dev-banner">开发模式</div>
        {% endif %}
    """
    manifest = load_manifest()
    return not bool(manifest)


@register.simple_tag
def vite_dev_server_url():
    """
    HJJ: 获取Vite开发服务器URL
    
    返回:
        str - 开发服务器URL，默认 http://localhost:5173
    
    用法:
        {% vite_dev_server_url %}
    """
    return getattr(settings, 'VITE_DEV_SERVER_URL', 'http://localhost:5173')