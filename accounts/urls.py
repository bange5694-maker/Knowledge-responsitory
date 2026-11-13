# ZYH: 模块功能：账户应用的 URL 路由，把登录、注册、退出、结果页、找回密码映射到对应视图。

from django.urls import path
from django.urls import re_path

from . import views
from .forms import LoginForm

# ZYH: 命名空间，模板中可用 {% url 'accounts:login' %} 等方式反向解析。
app_name = "accounts"

# ZYH: 账户模块路由表，统一以 accounts 作为 URL 命名空间。
urlpatterns = [re_path(r'^login/$',
                       views.LoginView.as_view(success_url='/'),
                       name='login',
                       kwargs={'authentication_form': LoginForm}),
               # ZYH: 注册页，提交后由 RegisterView 处理。
               re_path(r'^register/$',
                       views.RegisterView.as_view(success_url="/"),
                       name='register'),
               # ZYH: 退出登录，由 LogoutView 清理会话后跳回登录页。
               re_path(r'^logout/$',
                       views.LogoutView.as_view(),
                       name='logout'),
               # ZYH: 注册/邮箱验证结果页。
               path(r'account/result.html',
                    views.account_result,
                    name='result'),
               # ZYH: 找回密码页，展示并提交新密码表单。
               re_path(r'^forget_password/$',
                       views.ForgetPasswordView.as_view(),
                       name='forget_password'),
               # ZYH: 发送找回密码邮箱验证码的接口。
               re_path(r'^forget_password_code/$',
                       views.ForgetPasswordEmailCode.as_view(),
                       name='forget_password_code'),
               ]
