# XJN: 模块功能：评论模板标签库，提供评论树递归展开与单条评论渲染的模板标签。
from django import template

register = template.Library()


# XJN: 功能：递归收集当前评论下所有已启用的子评论（深度优先顺序），供模板展开评论树。
# XJN: 入参 commentlist：文章全部评论的 QuerySet；comment：当前评论对象。
# XJN: 返回值：list[Comment]，按递归顺序排列的全部后代评论。
@register.simple_tag
def parse_commenttree(commentlist, comment):
    """获得当前评论子评论的列表
        用法: {% parse_commenttree article_comments comment as childcomments %}
    """
    datas = []

    # XJN: 内部递归函数：先收集 c 的直接子评论，再对每个子评论继续递归，实现多级嵌套展开。
    # XJN: 入参 c：当前层级的评论；返回值：无（结果累积到外层 datas）。
    def parse(c):
        # XJN: 只取已启用（审核通过）的子评论；过滤放在循环内会随层级重复查询。
        childs = commentlist.filter(parent_comment=c, is_enable=True)
        for child in childs:
            datas.append(child)
            # XJN: 递归处理子评论的子评论，从而支持任意层级回复。
            parse(child)

    parse(comment)
    return datas


# XJN: 功能：渲染单条评论的 inclusion tag，供评论列表模板复用。
# XJN: 入参 comment：Comment 实例；ischild：bool，是否为子评论（影响缩进层级）。
# XJN: 返回值：dict 上下文，含 comment_item 与 depth，交由 comment_item.html 渲染。
@register.inclusion_tag('comments/tags/comment_item.html')
def show_comment_item(comment, ischild):
    """评论"""
    # XJN: 子评论层级为 1，顶级评论层级为 2，用于模板中的缩进样式。
    depth = 1 if ischild else 2
    return {
        'comment_item': comment,
        'depth': depth
    }
