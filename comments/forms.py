# XJN: 模块功能：定义评论提交表单 CommentForm，基于 Comment 模型只接收正文，
# XJN: 并额外提供隐藏的父评论 ID 字段用于提交回复。
from django import forms
from django.forms import ModelForm

from .models import Comment


# XJN: 评论表单类：继承 ModelForm，绑定 Comment 模型的 body 字段，负责评论/回复提交数据的校验与保存。
# XJN: 实例化入参：data（POST 数据）、可选 files/instance 等标准 ModelForm 参数。
# XJN: 调用返回值：表单实例，cleaned_data 中含 body 与 parent_comment_id。
class CommentForm(ModelForm):
    # XJN: 隐藏字段：承载回复目标评论的主键；非必填，空值表示这是一条顶级评论。
    parent_comment_id = forms.IntegerField(
        widget=forms.HiddenInput, required=False)

    # XJN: 表单元信息：指定绑定模型 Comment，仅暴露 body 一个可编辑字段（作者、文章、审核状态由视图赋值）。
    class Meta:
        model = Comment
        fields = ['body']
