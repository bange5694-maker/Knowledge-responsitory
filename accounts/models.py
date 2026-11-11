# ZYH: 模块功能：定义博客用户模型 BlogUser，在 Django 内置用户模型基础上扩展昵称、创建/修改时间与来源字段。

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from djangoblog.utils import get_current_site


# Create your models here.

# ZYH: BlogUser 继承 AbstractUser，复用用户名、密码、邮箱等认证字段，并补充博客业务所需字段。
class BlogUser(AbstractUser):
    # ZYH: 昵称，用于前台作者信息展示；blank=True 表示允许为空。
    nickname = models.CharField(_('nick name'), max_length=100, blank=True)
    # ZYH: 用户创建时间，默认取当前时间，便于后台按注册时间排序与统计。
    creation_time = models.DateTimeField(_('creation time'), default=now)
    # ZYH: 用户信息最后修改时间，默认取当前时间，后续可在保存时手动更新。
    last_modify_time = models.DateTimeField(_('last modify time'), default=now)
    # ZYH: 用户来源，例如 Register、adminsite，用于区分注册渠道。
    source = models.CharField(_('create source'), max_length=100, blank=True)

    # ZYH: 返回当前用户在博客前台的作者详情页地址，供模板链接和邮件中的地址拼接使用。
    def get_absolute_url(self):
        # ZYH: 通过 blog:author_detail 路由反向解析，kwargs 中的 author_name 取当前用户名。
        return reverse(
            'blog:author_detail', kwargs={
                'author_name': self.username})

    # ZYH: 定义对象的字符串表示，后台和日志中统一显示邮箱，便于识别用户。
    def __str__(self):
        return self.email

    # ZYH: 拼接当前用户的完整外链地址（协议 + 站点域名 + 作者页路径），用于邮件等外部场景。
    def get_full_url(self):
        # ZYH: 从站点配置中取当前域名，避免在代码里写死域名。
        site = get_current_site().domain
        url = "https://{site}{path}".format(site=site,
                                            path=self.get_absolute_url())
        return url

    # ZYH: 模型元信息：默认按 id 倒序排列，并设置后台显示名称与“取最新”字段。
    class Meta:
        ordering = ['-id']
        verbose_name = _('user')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
