# XJN: 模块功能：评论视图层，提供评论/回复提交视图（CommentPostView）与评论表情回应接口（CommentReactionView），
# XJN: 负责登录校验、文章评论开关校验、审核状态设置以及表情回应的切换与统计返回。
# Create your views here.
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from accounts.models import BlogUser
from blog.models import Article
from djangoblog.base_views import AuthenticatedFormView
from .forms import CommentForm
from .models import Comment, CommentReaction


# XJN: 评论提交视图类：处理文章评论与回复的 GET 跳转和 POST 提交。
# XJN: 类属性 form_class：评论表单 CommentForm；template_name：校验失败时回显的模板。
# XJN: 入参：URL 中携带 article_id；返回值：重定向响应或渲染后的文章详情页。
class CommentPostView(AuthenticatedFormView):
    """
    评论提交视图

    使用 AuthenticatedFormView 基类，自动提供：
    - 登录验证（未登录用户会被重定向）
    - CSRF 保护
    """
    form_class = CommentForm
    template_name = 'blog/article_detail.html'

    # XJN: 功能：GET 请求不提交评论，直接跳转回文章详情页的 #comments 锚点。
    # XJN: 入参 request：HttpRequest；*args/**kwargs 中含 article_id。
    # XJN: 返回值：HttpResponseRedirect，指向文章详情页评论区。
    def get(self, request, *args, **kwargs):
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)
        url = article.get_absolute_url()
        return HttpResponseRedirect(url + "#comments")

    # XJN: 功能：表单校验失败时，带原表单与文章对象重新渲染详情页。
    # XJN: 入参 request：HttpRequest；form：校验失败的 CommentForm 实例。
    # XJN: 返回值：TemplateResponse，包含 form 与 article 上下文。
    def form_invalid(self, form):
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)

        return self.render_to_response({
            'form': form,
            'article': article
        })

    # XJN: 功能：评论表单校验通过后保存评论，并处理父评论关联与是否立即展示。
    # XJN: 入参 form：校验通过的 CommentForm；依赖 request.user 与 URL 中的 article_id。
    # XJN: 返回值：HttpResponseRedirect，跳转到新评论所在位置；文章关闭评论时抛出 ValidationError。
    def form_valid(self, form):
        """提交的数据验证合法后的逻辑"""
        user = self.request.user
        author = BlogUser.objects.get(pk=user.pk)
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)

        # XJN: 文章评论开关或文章状态为关闭（'c'）时，禁止提交评论。
        if article.comment_status == 'c' or article.status == 'c':
            raise ValidationError("该文章评论已关闭.")
        # XJN: 先不落库，补充文章、作者、审核状态等非表单字段后再保存。
        comment = form.save(False)
        comment.article = article
        from djangoblog.utils import get_blog_setting
        settings = get_blog_setting()
        # XJN: 站点未开启「评论需审核」时，评论直接置为可见。
        if not settings.comment_need_review:
            comment.is_enable = True
        comment.author = author

        # XJN: 若表单携带 parent_comment_id，则将其作为父评论，形成嵌套回复关系。
        if form.cleaned_data['parent_comment_id']:
            parent_comment = Comment.objects.get(
                pk=form.cleaned_data['parent_comment_id'])
            comment.parent_comment = parent_comment

        # XJN: 保存评论并触发模型保存后的相关逻辑（如清理缓存/通知），随后重定向到该评论锚点。
        comment.save(True)
        return HttpResponseRedirect(
            "%s#div-comment-%d" %
            (article.get_absolute_url(), comment.pk))


# XJN: 评论表情回应视图类：GET 获取某评论的表情统计，POST 切换当前用户的表情回应。
# XJN: 入参：URL 中携带 comment_id；返回值：JsonResponse（成功/错误信息与最新 reactions 数据）。
class CommentReactionView(View):
    """
    评论 Emoji 反应 API
    GET /comment/<comment_id>/react - 获取 reactions（公开）
    POST /comment/<comment_id>/react - 切换 reaction（需要登录）
    """

    # XJN: 功能：查询指定评论的表情回应汇总，允许匿名访问。
    # XJN: 入参 request：HttpRequest；comment_id：评论主键。
    # XJN: 返回值：JsonResponse，success=True 与 reactions 统计字典；评论不存在或未启用时返回 404。
    def get(self, request, comment_id):
        """获取评论的 reactions 数据（公开访问）"""
        comment = get_object_or_404(Comment, id=comment_id, is_enable=True)

        # 传递用户信息，如果未登录则传递 None
        user = request.user if request.user.is_authenticated else None
        reactions_data = comment.get_reactions_summary(user)

        return JsonResponse({
            'success': True,
            'reactions': reactions_data
        })

    # XJN: 功能：为当前登录用户添加或取消某条评论上的指定表情回应，并返回最新统计。
    # XJN: 入参 request：HttpRequest（POST 中需含 reaction_type）；comment_id：评论主键。
    # XJN: 返回值：JsonResponse，含 success、action（added/removed）与 reactions；未登录返回 401，表情非法返回 400。
    def post(self, request, comment_id):
        # POST 需要登录验证
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        # 获取评论（只有已启用的评论才能点赞）
        comment = get_object_or_404(Comment, id=comment_id, is_enable=True)

        # 获取 reaction 类型
        reaction_type = request.POST.get('reaction_type')

        # 验证 reaction_type 是否合法
        valid_reactions = [choice[0] for choice in CommentReaction.REACTION_CHOICES]
        if reaction_type not in valid_reactions:
            return JsonResponse({
                'error': 'Invalid reaction type'
            }, status=400)

        # 切换 reaction（如果已存在则删除，否则创建）
        # XJN: 先尝试取回已有记录：不存在则创建（点赞），已存在则删除（取消点赞），实现切换语义。
        reaction, created = CommentReaction.objects.get_or_create(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type
        )

        if not created:
            # 已存在，删除它（取消点赞）
            # XJN: 命中 (comment, user, reaction_type) 唯一约束，说明此前已回应，此处执行取消。
            reaction.delete()
            action = 'removed'
        else:
            # XJN: 新建成功，表示本次为新增回应。
            action = 'added'

        # 返回该评论的所有 reactions 统计
        # XJN: 重新汇总全部表情，返回给前端整体刷新各表情的计数与高亮状态。
        reactions_data = comment.get_reactions_summary(request.user)

        return JsonResponse({
            'success': True,
            'action': action,
            'reactions': reactions_data
        })
