# ZYH: 模块功能：账户相关表单，负责登录、注册、找回密码的字段渲染与数据校验。

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import widgets
from django.utils.translation import gettext_lazy as _
from . import utils
from .models import BlogUser


# ZYH: 登录表单，复用 Django 的 AuthenticationForm，仅调整输入框样式与占位提示。
class LoginForm(AuthenticationForm):
    # ZYH: 初始化父类表单后，为用户名和密码控件补充 Bootstrap 样式与 placeholder。
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = widgets.TextInput(
            attrs={'placeholder': "username", "class": "form-control"})
        self.fields['password'].widget = widgets.PasswordInput(
            attrs={'placeholder': "password", "class": "form-control"})


# ZYH: 注册表单，在 UserCreationForm 基础上增加邮箱字段并校验邮箱唯一性。
class RegisterForm(UserCreationForm):
    # ZYH: 初始化表单，统一设置用户名、邮箱、两次密码输入框的样式与提示。
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget = widgets.TextInput(
            attrs={'placeholder': "username", "class": "form-control"})
        self.fields['email'].widget = widgets.EmailInput(
            attrs={'placeholder': "email", "class": "form-control"})
        self.fields['password1'].widget = widgets.PasswordInput(
            attrs={'placeholder': "password", "class": "form-control"})
        self.fields['password2'].widget = widgets.PasswordInput(
            attrs={'placeholder': "repeat password", "class": "form-control"})

    # ZYH: 校验邮箱是否已被注册；返回清洗后的邮箱，重复时抛出 ValidationError。
    def clean_email(self):
        email = self.cleaned_data['email']
        # ZYH: 用 get_user_model() 查询，兼容自定义用户模型。
        if get_user_model().objects.filter(email=email).exists():
            raise ValidationError(_("email already exists"))
        return email

    # ZYH: 指定表单对应的模型与允许用户填写的字段。
    class Meta:
        model = get_user_model()
        fields = ("username", "email")


# ZYH: 找回密码表单，收集新密码、确认密码、邮箱和邮箱验证码。
class ForgetPasswordForm(forms.Form):
    # ZYH: 新密码字段，使用 PasswordInput 隐藏输入内容。
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                'placeholder': _("New password")
            }
        ),
    )

    # ZYH: 确认密码字段，用于防止用户输错新密码。
    new_password2 = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                'placeholder': _("Confirm password")
            }
        ),
    )

    # ZYH: 邮箱字段，用于定位要重置密码的账户。
    email = forms.EmailField(
        label='邮箱',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _("Email")
            }
        ),
    )

    # ZYH: 邮箱验证码字段，由 ForgetPasswordEmailCode 视图发送、缓存校验。
    code = forms.CharField(
        label=_('Code'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _("Code")
            }
        ),
    )

    # ZYH: 校验两次新密码是否一致，并调用 Django 密码强度校验；通过后返回确认密码。
    def clean_new_password2(self):
        password1 = self.data.get("new_password1")
        password2 = self.data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("passwords do not match"))
        # ZYH: 复用 Django 的密码强度规则，避免弱密码通过校验。
        password_validation.validate_password(password2)

        return password2

    # ZYH: 校验邮箱必须已注册；返回清洗后的邮箱，未注册时抛出 ValidationError。
    def clean_email(self):
        user_email = self.cleaned_data.get("email")
        if not BlogUser.objects.filter(
                email=user_email
        ).exists():
            # todo 这里的报错提示可以判断一个邮箱是不是注册过，如果不想暴露可以修改
            raise ValidationError(_("email does not exist"))
        return user_email

    # ZYH: 调用 utils.verify 校验验证码；错误信息非空时抛出 ValidationError，通过则返回验证码。
    def clean_code(self):
        code = self.cleaned_data.get("code")
        error = utils.verify(
            email=self.cleaned_data.get("email"),
            code=code,
        )
        if error:
            raise ValidationError(error)
        return code


# ZYH: 仅收集邮箱的表单，供“发送找回密码验证码”接口使用。
class ForgetPasswordCodeForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
    )
