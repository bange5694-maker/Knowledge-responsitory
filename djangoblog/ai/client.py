import logging

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """AI 调用失败时抛出的统一异常。"""


class AIClient:
    """DeepSeek 等 OpenAI 兼容接口的轻量封装。"""

    @classmethod
    def chat(cls, messages, temperature=0.3, max_tokens=None) -> str:
        # DH: 每次调用都实时读取 settings，保证 override_settings 生效
        if not getattr(settings, 'AI_ENABLED', False):
            raise AIClientError('AI 功能未启用')
        api_key = (getattr(settings, 'AI_API_KEY', '') or '').strip()
        if not api_key:
            raise AIClientError('AI API Key 未配置')

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=getattr(
                    settings, 'AI_BASE_URL', 'https://api.deepseek.com'),
                timeout=settings.AI_TIMEOUT,
                max_retries=2,
            )
            response = client.chat.completions.create(
                model=getattr(settings, 'AI_MODEL', 'deepseek-chat'),
                messages=messages,
                temperature=temperature,
                max_tokens=(
                    max_tokens
                    if max_tokens is not None
                    else getattr(settings, 'AI_MAX_TOKENS', 800)
                ),
            )
            content = response.choices[0].message.content
        except Exception as exc:
            # DH: 只记录异常类型，避免日志/异常消息泄露 API Key
            logger.warning('AI 调用失败: %s', type(exc).__name__)
            raise AIClientError(
                'AI 调用失败: %s' % type(exc).__name__) from None

        text = str(content).strip() if content is not None else ''
        if not text:
            raise AIClientError('AI 返回内容为空')
        return text
