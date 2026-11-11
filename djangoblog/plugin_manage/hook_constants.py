# DH: 这个文件是插件用的钩子名字，相当于插件和主程序约定好的“暗号”，两边都从这里 import，防止写错。

ARTICLE_DETAIL_LOAD = 'article_detail_load'
ARTICLE_CREATE = 'article_create'
ARTICLE_UPDATE = 'article_update'
ARTICLE_DELETE = 'article_delete'

# DH: 文章正文那个钩子的名字，阅读时间、版权这些插件都挂在它上面。
ARTICLE_CONTENT_HOOK_NAME = "the_content"

# 位置钩子常量
# DH: 页面位置钩子，插件可以把内容插到文章顶部、底部、侧边栏这些地方。
POSITION_HOOKS = {
    'article_top': 'article_top_widgets',
    'article_bottom': 'article_bottom_widgets',
    'sidebar': 'sidebar_widgets',
    'header': 'header_widgets',
    'footer': 'footer_widgets',
    'comment_before': 'comment_before_widgets',
    'comment_after': 'comment_after_widgets',
}

# 资源注入钩子
# DH: 往页面 head 和 body 里加 css/js 的钩子。
HEAD_RESOURCES_HOOK = 'head_resources'
BODY_RESOURCES_HOOK = 'body_resources'
