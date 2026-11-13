# XJN: 模块功能：定义评论（Comment）与评论表情回应（CommentReaction）数据模型，
# XJN: 包含字段约束、排序规则、查询索引与表情统计方法。
from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from blog.models import Article


# Create your models here.

# XJN: 评论模型：保存某位用户在指定文章下的评论正文，并通过自关联 parent_comment 支持多级回复。
class Comment(models.Model):
    # XJN: 字段说明：body 为评论正文，最大长度 300。
    body = models.TextField('正文', max_length=300)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_modify_time = models.DateTimeField(_('last modify time'), default=now)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.CASCADE)
    article = models.ForeignKey(
        Article,
        verbose_name=_('article'),
        on_delete=models.CASCADE)
    # XJN: 父评论自关联：为空表示顶级评论，非空表示对某条评论的回复。
    parent_comment = models.ForeignKey(
        'self',
        verbose_name=_('parent comment'),
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    # XJN: 展示开关：默认 False 表示待审核/隐藏，提交时按站点评论审核设置决定是否置为 True。
    is_enable = models.BooleanField(_('enable'),
                                    default=False, blank=False, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = _('comment')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
        indexes = [
            # 优化评论列表查询：article + parent_comment + is_enable组合索引
            models.Index(fields=['article', 'parent_comment', 'is_enable'], name='idx_art_parent_enable'),
            # 优化侧边栏评论查询：is_enable + id组合索引
            models.Index(fields=['is_enable', '-id'], name='idx_enable_id'),
        ]

    # XJN: 功能：返回该评论的字符串表示，便于后台与调试展示。
    # XJN: 入参：无（使用模型实例自身数据）。
    # XJN: 返回值：str，即评论正文。
    def __str__(self):
        return self.body

    # XJN: 功能：汇总当前评论各表情（reaction_type）的回应数量、前十位用户及当前用户是否已回应。
    # XJN: 入参 user：当前登录用户或 None，用于计算 has_reacted 标记。
    # XJN: 返回值：dict，键为表情符号，值为 {'count': int, 'has_reacted': bool, 'users': list[str]}。
    def get_reactions_summary(self, user=None):
        """
        获取评论的 reactions 统计信息
        返回格式: {
            '👍': {
                'count': 5,
                'has_reacted': True,
                'users': ['Alice', 'Bob', 'Charlie']
            },
            '❤️': {'count': 3, 'has_reacted': False, 'users': [...]},
            ...
        }
        """
        from django.db.models import Count

        # XJN: 按表情类型聚合，一次性统计每种表情的回应总数。
        reactions = CommentReaction.objects.filter(
            comment=self
        ).values('reaction_type').annotate(count=Count('id'))

        result = {}
        for reaction in reactions:
            emoji = reaction['reaction_type']

            # 获取该 emoji 的所有点赞用户
            reaction_users = CommentReaction.objects.filter(
                comment=self,
                reaction_type=emoji
            ).select_related('user')[:10]  # 最多显示10个用户

            user_names = [r.user.nickname or r.user.username for r in reaction_users]

            result[emoji] = {
                'count': reaction['count'],
                'has_reacted': False,
                'users': user_names
            }

            # XJN: 仅当存在登录用户时，逐种表情判断该用户是否已回应（会带来额外查询开销）。
            if user and user.is_authenticated:
                result[emoji]['has_reacted'] = CommentReaction.objects.filter(
                    comment=self,
                    user=user,
                    reaction_type=emoji
                ).exists()

        return result


# XJN: 表情回应模型：记录某用户对某条评论选择的 Emoji 反应，同用户同评论同表情唯一。
class CommentReaction(models.Model):
    """
    评论的 Emoji 反应/点赞
    """
    # XJN: 可选的八种 Emoji 反应类型，供前端与后台校验使用。
    REACTION_CHOICES = [
        ('👍', 'thumbs_up'),
        ('👎', 'thumbs_down'),
        ('❤️', 'heart'),
        ('😄', 'laugh'),
        ('🎉', 'hooray'),
        ('😕', 'confused'),
        ('🚀', 'rocket'),
        ('👀', 'eyes'),
    ]

    comment = models.ForeignKey(
        Comment,
        verbose_name=_('comment'),
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.CASCADE
    )
    reaction_type = models.CharField(
        _('reaction type'),
        max_length=10,
        choices=REACTION_CHOICES
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('comment reaction')
        verbose_name_plural = _('comment reactions')
        # 每个用户对同一评论的同一种 emoji 只能点一次
        # XJN: 数据库层唯一约束，防止同一用户对同一评论重复提交同种表情。
        unique_together = ['comment', 'user', 'reaction_type']
        indexes = [
            # XJN: 按评论 + 表情建立索引，加速 reactions 统计查询。
            models.Index(fields=['comment', 'reaction_type'], name='idx_comment_reaction'),
        ]

    # XJN: 功能：返回表情回应的可读字符串表示。
    # XJN: 入参：无（使用模型实例自身数据）。
    # XJN: 返回值：str，格式为「用户名 - 表情 on comment 评论ID」。
    def __str__(self):
        return f'{self.user.username} - {self.reaction_type} on comment {self.comment.id}'
