# ZYH: 模块功能：账户验证码工具，负责发送找回密码邮件、写入缓存并在校验时读取缓存。

import typing
from datetime import timedelta

from django.core.cache import cache
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from djangoblog.utils import send_email

# ZYH: 验证码统一有效期：5 分钟，超时后缓存自动失效。
_code_ttl = timedelta(minutes=5)


# ZYH: 发送找回密码验证码邮件。
# ZYH: 参数 to_mail 为收件邮箱，code 为验证码，subject 为邮件主题（默认“Verify Email”）。
# ZYH: 无返回值；底层 send_email 发送失败时可能抛出异常，由调用方处理。
def send_verify_email(to_mail: str, code: str, subject: str = _("Verify Email")):
    """发送重设密码验证码
    Args:
        to_mail: 接受邮箱
        subject: 邮件主题
        code: 验证码
    """
    # ZYH: 邮件正文说明验证码用途及 5 分钟有效期，避免用户泄露验证码。
    html_content = _(
        "You are resetting the password, the verification code is：%(code)s, valid within 5 minutes, please keep it "
        "properly") % {'code': code}
    send_email([to_mail], subject, html_content)


# ZYH: 校验邮箱与验证码是否匹配。
# ZYH: 参数 email 为请求邮箱，code 为用户提交的验证码。
# ZYH: 校验通过返回 None，失败返回可直接展示的错误文案。
def verify(email: str, code: str) -> typing.Optional[str]:
    """验证code是否有效
    Args:
        email: 请求邮箱
        code: 验证码
    Return:
        如果有错误就返回错误str
    Node:
        这里的错误处理不太合理，应该采用raise抛出
        否测调用方也需要对error进行处理
    """
    # ZYH: 从缓存读取该邮箱对应的验证码，缓存不存在或已过期时返回 None。
    cache_code = get_code(email)
    if cache_code != code:
        return gettext("Verification code error")


# ZYH: 将验证码写入缓存，键为邮箱、值为验证码，过期时间取 _code_ttl 的秒数（300 秒）。
def set_code(email: str, code: str):
    """设置code"""
    cache.set(email, code, _code_ttl.seconds)


# ZYH: 按邮箱从缓存读取验证码；不存在或已过期时返回 None。
def get_code(email: str) -> typing.Optional[str]:
    """获取code"""
    return cache.get(email)
