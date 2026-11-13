# ZYH: 模块功能：账户相关视图，含注册、登录、退出、找回密码、邮箱激活与结果页。

import logging
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from djangoblog.utils import send_email, get_sha256, get_current_site, generate_code, delete_sidebar_cache
from djangoblog.base_views import SecureFormView, LoginFormView, LogoutRedirectView
from . import utils
from .forms import RegisterForm, LoginForm, ForgetPasswordForm, ForgetPasswordCodeForm
from .models import BlogUser

# ZYH: 账户模块日志器，记录注册、登录、激活等关键行为，便于排查问题。
logger = logging.getLogger(__name__)


# Create your views here.

# ZYH: 用户注册视图：校验注册表单，创建未激活用户并发送邮箱激活链接。
class RegisterView(SecureFormView):
    """
    用户注册视图（重构版）

    使用 SecureFormView 基类，自动提供 CSRF 保护
    """
    form_class = RegisterForm
    template_name = 'account/registration_form.html'

    # ZYH: 表单校验通过后的处理：落库、生成激活链接、发送验证邮件并跳转结果页。
    # ZYH: 参数 form 为已通过基础校验的 RegisterForm；返回 HTTP 重定向或带错误提示的响应。
    def form_valid(self, form):
        if form.is_valid():
            user = form.save(False)
            # ZYH: 注册后先标记为未激活，必须完成邮箱验证后才能登录。
            user.is_active = False
            user.source = 'Register'
            user.save(True)
            site = get_current_site().domain
            # ZYH: 使用 SECRET_KEY 与用户 id 做两次 SHA256，生成不可伪造的激活签名。
            sign = get_sha256(get_sha256(settings.SECRET_KEY + str(user.id)))

            # ZYH: 开发环境固定用本地地址，避免激活链接指向线上域名。
            if settings.DEBUG:
                site = '127.0.0.1:8000'
            path = reverse('account:result')
            # ZYH: 激活链接携带 type=validation、用户 id 与签名，供结果页校验。
            url = "http://{site}{path}?type=validation&id={id}&sign={sign}".format(
                site=site, path=path, id=user.id, sign=sign)

            content = """
                            <p>请点击下面链接验证您的邮箱</p>

                            <a href="{url}" rel="bookmark">{url}</a>

                            再次感谢您！
                            <br />
                            如果上面链接无法打开，请将此链接复制至浏览器。
                            {url}
                            """.format(url=url)
            # ZYH: 发送激活邮件到用户注册时填写的邮箱。
            send_email(
                emailto=[
                    user.email,
                ],
                title='验证您的电子邮箱',
                content=content)

            # ZYH: 跳转到注册结果页，提示用户前往邮箱完成验证。
            url = reverse('accounts:result') + \
                  '?type=register&id=' + str(user.id)
            return HttpResponseRedirect(url)
        else:
            return self.render_to_response({
                'form': form
            })


# ZYH: 用户退出视图：清理服务端会话、侧边栏缓存和登录标记 Cookie。
class LogoutView(LogoutRedirectView):
    """
    用户登出视图（重构版）

    使用 LogoutRedirectView 基类，自动禁用缓存
    """
    url = '/login/'

    # ZYH: 处理退出请求：先注销会话，再删除缓存与 logged_user Cookie，最后交给父类重定向。
    def get(self, request, *args, **kwargs):
        logout(request)
        delete_sidebar_cache()
        # 获取响应对象并删除登录标记 cookie
        response = super(LogoutView, self).get(request, *args, **kwargs)
        response.delete_cookie('logged_user')
        return response


# ZYH: 用户登录视图：校验账号密码、建立登录会话，并按“记住我”设置会话与 Cookie 有效期。
class LoginView(LoginFormView):
    """
    用户登录视图（重构版）

    使用 LoginFormView 基类，自动提供：
    - 敏感参数保护（password）
    - CSRF 保护
    - 禁用缓存
    """
    form_class = LoginForm
    template_name = 'account/login.html'
    success_url = '/'
    redirect_field_name = REDIRECT_FIELD_NAME

    # ZYH: 向模板上下文补充登录成功后的跳转地址；未提供时默认回首页。
    def get_context_data(self, **kwargs):
        redirect_to = self.request.GET.get(self.redirect_field_name)
        if redirect_to is None:
            redirect_to = '/'
        kwargs['redirect_to'] = redirect_to

        return super(LoginView, self).get_context_data(**kwargs)

    # ZYH: 处理登录表单提交：验证账号密码、建立会话、设置登录有效期与 logged_user 标记。
    # ZYH: 参数 form 为 LoginForm；校验失败时返回带错误信息的登录页。
    def form_valid(self, form):
        form = AuthenticationForm(data=self.request.POST, request=self.request)

        if form.is_valid():
            delete_sidebar_cache()
            logger.info(self.redirect_field_name)

            # ZYH: 调用 Django 认证体系建立登录会话，后续请求通过 session 识别用户。
            auth.login(self.request, form.get_user())
            # 设置登录有效期
            if self.request.POST.get("remember"):
                # ZYH: 勾选“记住我”时使用配置的长期有效期。
                self.request.session.set_expiry(settings.REMEMBER_ME_LOGIN_TTL)
                cookie_max_age = settings.REMEMBER_ME_LOGIN_TTL
            else:
                # 使用Django默认的2周
                # ZYH: 未勾选时使用 Django 默认的会话有效期。
                self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                cookie_max_age = settings.SESSION_COOKIE_AGE

            # 获取响应对象并设置登录标记 cookie
            response = super(LoginView, self).form_valid(form)
            # ZYH: 写入前端可读的 logged_user 标记，供页面判断登录状态。
            response.set_cookie(
                'logged_user',
                'true',
                max_age=cookie_max_age,
                httponly=False,  # 允许 JavaScript 访问
                samesite='Lax'
            )
            return response
            # return HttpResponseRedirect('/')
        else:
            return self.render_to_response({
                'form': form
            })

    # ZYH: 计算登录成功后的跳转地址，并校验目标域名，防止开放重定向。
    def get_success_url(self):

        redirect_to = self.request.POST.get(self.redirect_field_name)
        if not url_has_allowed_host_and_scheme(
                url=redirect_to, allowed_hosts=[
                    self.request.get_host()]):
            redirect_to = self.success_url
        return redirect_to


# ZYH: 账户结果页：展示注册成功提示，或校验签名并激活邮箱。
# ZYH: 参数 request 需携带 type（register/validation）、id；验证时还需 sign。
def account_result(request):
    type = request.GET.get('type')
    id = request.GET.get('id')

    # ZYH: 根据 id 查用户，不存在时直接返回 404。
    user = get_object_or_404(get_user_model(), id=id)
    logger.info(type)
    if user.is_active:
        return HttpResponseRedirect('/')
    if type and type in ['register', 'validation']:
        if type == 'register':
            content = '''
    恭喜您注册成功，一封验证邮件已经发送到您的邮箱，请验证您的邮箱后登录本站。
    '''
            title = '注册成功'
        else:
            # ZYH: 重新计算签名并与 URL 中的 sign 比对，防止伪造激活链接。
            c_sign = get_sha256(get_sha256(settings.SECRET_KEY + str(user.id)))
            sign = request.GET.get('sign')
            if sign != c_sign:
                return HttpResponseForbidden()
            # ZYH: 签名正确后把用户置为激活状态并保存，完成邮箱验证。
            user.is_active = True
            user.save()
            content = '''
            恭喜您已经成功的完成邮箱验证，您现在可以使用您的账号来登录本站。
            '''
            title = '验证成功'
        return render(request, 'account/result.html', {
            'title': title,
            'content': content
        })
    else:
        return HttpResponseRedirect('/')


# ZYH: 找回密码视图：校验邮箱、验证码和两次新密码，通过后直接重置密码。
class ForgetPasswordView(SecureFormView):
    """
    忘记密码视图（重构版）

    使用 SecureFormView 基类，自动提供 CSRF 保护
    """
    form_class = ForgetPasswordForm
    template_name = 'account/forget_password.html'

    # ZYH: 表单校验通过后按邮箱取出用户，写入新密码哈希并跳转登录页。
    # ZYH: 参数 form 为 ForgetPasswordForm；用户不存在等异常由表单校验提前拦截。
    def form_valid(self, form):
        if form.is_valid():
            blog_user = BlogUser.objects.filter(email=form.cleaned_data.get("email")).get()
            # ZYH: 使用 make_password 生成哈希后再保存，禁止保存明文密码。
            blog_user.password = make_password(form.cleaned_data["new_password2"])
            blog_user.save()
            return HttpResponseRedirect('/login/')
        else:
            return self.render_to_response({'form': form})


# ZYH: 发送找回密码验证码的接口视图，只接受 POST 请求。
class ForgetPasswordEmailCode(View):

    # ZYH: 校验邮箱表单，生成随机验证码，先发邮件再写入缓存（5 分钟有效）。
    # ZYH: 参数 request 为 POST 请求；表单无效返回错误提示，成功返回 "ok"。
    def post(self, request: HttpRequest):
        form = ForgetPasswordCodeForm(request.POST)
        if not form.is_valid():
            return HttpResponse("错误的邮箱")
        to_email = form.cleaned_data["email"]

        # ZYH: 生成随机验证码并通过邮件发送给用户。
        code = generate_code()
        utils.send_verify_email(to_email, code)
        # ZYH: 将验证码写入缓存，后续 clean_code 会在 5 分钟内校验。
        utils.set_code(to_email, code)

        return HttpResponse("ok")
