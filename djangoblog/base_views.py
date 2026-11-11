#!/usr/bin/env python
# encoding: utf-8
# DH: 这个文件把几个常用的页面基类写好，别的页面继承它们，就不用每次都重复写 CSRF、登录检查这些。

"""
Django Blog 基础视图类
提供带有常用装饰器的视图基类，减少重复的 dispatch 方法定义
"""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView


# DH: 带 CSRF 保护的表单页面基类，别的表单页面继承它就行。
class SecureFormView(FormView):
    """
    安全的 FormView 基类

    自动添加 CSRF 保护，适用于所有需要表单提交的视图

    Usage:
        class MyFormView(SecureFormView):
            form_class = MyForm
            template_name = 'my_form.html'

            def form_valid(self, form):
                # 处理表单数据
                return super().form_valid(form)
    """

    # DH: 提交表单时自动检查 CSRF，防止别人伪造提交。
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        """添加 CSRF 保护"""
        return super().dispatch(*args, **kwargs)


# DH: 需要先登录才能用的表单页面。
class AuthenticatedFormView(FormView):
    """
    需要登录的 FormView

    自动检查用户登录状态并添加 CSRF 保护
    未登录用户会被重定向到登录页面

    Usage:
        class MyAuthFormView(AuthenticatedFormView):
            form_class = MyForm
            template_name = 'my_form.html'
    """

    # DH: 没登录会跳去登录页，同时也做 CSRF 检查。
    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        """添加登录要求和 CSRF 保护"""
        return super().dispatch(*args, **kwargs)


# DH: 登录页专用的表单页面，多加了几个保护。
class LoginFormView(FormView):
    """
    登录专用 FormView

    包含以下保护措施：
    - 敏感参数保护（password 等）
    - CSRF 保护
    - 禁用缓存（防止登录状态被缓存）

    Usage:
        class LoginView(LoginFormView):
            form_class = LoginForm
            template_name = 'login.html'

            def form_valid(self, form):
                # 处理登录逻辑
                return super().form_valid(form)
    """

    # DH: 密码不写进日志；提交要验 CSRF；页面不让浏览器缓存，防止退出后还能点回去。
    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """添加敏感参数保护、CSRF 保护和禁用缓存"""
        return super().dispatch(request, *args, **kwargs)


# DH: 退出登录用的跳转页面。
class LogoutRedirectView(RedirectView):
    """
    登出专用 RedirectView

    自动禁用缓存，确保登出操作不会被缓存

    Usage:
        class LogoutView(LogoutRedirectView):
            url = '/login/'

            def get(self, request, *args, **kwargs):
                logout(request)
                return super().get(request, *args, **kwargs)
    """

    # DH: 退出后不让缓存，避免按后退键又回到登录状态。
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """禁用缓存"""
        return super().dispatch(request, *args, **kwargs)


# DH: 不想让浏览器缓存的表单页面，像验证码这种要实时刷新的地方用。
class NoCacheFormView(FormView):
    """
    禁用缓存的 FormView

    适用于需要实时数据的表单（如验证码、动态内容等）

    Usage:
        class MyCacheDisabledFormView(NoCacheFormView):
            form_class = MyForm
            template_name = 'my_form.html'
    """

    # DH: 页面不缓存，同时检查 CSRF。
    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        """禁用缓存并添加 CSRF 保护"""
        return super().dispatch(request, *args, **kwargs)
