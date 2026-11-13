# XJN: 模块功能：comments 应用的路由配置，声明评论提交与评论表情回应两个 URL 规则。
from django.urls import path

from . import views

# XJN: 应用命名空间，供模板中 {% url 'comments:xxx' %} 及反向解析使用。
app_name = "comments"
# XJN: 路由表：将 URL 映射到对应视图，并用 name 供反向解析。
urlpatterns = [
    # XJN: 评论/回复提交路由：POST 提交到指定文章评论区，name 为 postcomment。
    path(
        'article/<int:article_id>/postcomment',
        views.CommentPostView.as_view(),
        name='postcomment'),
    # XJN: 表情回应接口路由：GET 查询、POST 切换指定评论的 Emoji 反应，name 为 comment_react。
    path(
        'comment/<int:comment_id>/react',
        views.CommentReactionView.as_view(),
        name='comment_react'),
]
