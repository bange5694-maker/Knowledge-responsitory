# ZYH: 模块功能：账户应用的后台管理配置，注册 BlogUser 并定制新增/编辑表单与列表展示。

from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UsernameField
from django.utils.translation import gettext_lazy as _

# Register your models here.
from .models import BlogUser


# ZYH: 后台新增用户表单：要求两次输入密码，并在保存时写入哈希后的密码。
class BlogUserCreationForm(forms.ModelForm):
    # ZYH: 两次密码输入框，仅用于后台创建用户，不落库为模型字段。
    password1 = forms.CharField(label=_('password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Enter password again'), widget=forms.PasswordInput)

    # ZYH: 指定表单绑定的模型与可编辑字段。
    class Meta:
        model = BlogUser
        fields = ('email',)

    # ZYH: 校验两次输入的密码是否一致；一致返回 password2，否则抛出表单校验错误。
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("passwords do not match"))
        return password2

    # ZYH: 保存用户：先取未提交实例，用 set_password 生成哈希，再标记来源并落库。
    # ZYH: 参数 commit 为 False 时只构造对象不写库；返回用户对象。
    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.source = 'adminsite'
            user.save()
        return user


# ZYH: 后台编辑用户表单，复用 Django 的 UserChangeForm 并指定自定义用户模型。
class BlogUserChangeForm(UserChangeForm):
    # ZYH: 指定模型、字段及用户名字段类型。
    class Meta:
        model = BlogUser
        fields = '__all__'
        field_classes = {'username': UsernameField}

    # ZYH: 初始化父类表单，保留 UserChangeForm 的密码修改链接等行为。
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


# ZYH: 后台用户管理配置：列表展示昵称、邮箱、登录时间、注册时间与来源等字段。
class BlogUserAdmin(UserAdmin):
    form = BlogUserChangeForm
    add_form = BlogUserCreationForm
    # ZYH: 后台列表列，按 id、昵称、用户名、邮箱、登录时间、注册时间、来源展示。
    list_display = (
        'id',
        'nickname',
        'username',
        'email',
        'last_login',
        'date_joined',
        'source')
    # ZYH: 允许点击 id、用户名进入编辑页。
    list_display_links = ('id', 'username')
    # ZYH: 默认按 id 倒序，并支持用户名、昵称、邮箱搜索。
    ordering = ('-id',)
    search_fields = ('username', 'nickname', 'email')
