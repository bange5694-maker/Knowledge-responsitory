# 何君杰: AI 导读生成 service
# 契约：AI功能规格说明 §3.5/§3.7/§3.8；M1 §4.2

import json
import logging

from django.conf import settings
from django.utils.timezone import now

from djangoblog.ai import AIClient

logger = logging.getLogger(__name__)


# 何君杰: 导读提示词。只发标题和正文，要求输出严格 JSON。
SUMMARY_PROMPT = """你是一个博客导读助手。请只根据下面这篇文章的标题和正文，生成一份读前导读。

要求：
1. 只使用文章中出现的信息，不要编造文章没有的内容。
2. 摘要 80–120 字，说清这篇文章讲什么。
3. 三个看点，每条 20–40 字，必须来自文章具体内容，禁止“本文介绍了背景、方法和结论”这类空话。
4. 适合谁读 20–40 字，可为空；不要写“适合所有人”。
5. 关键词 3–5 个。
6. 输出必须是 JSON，不要输出 JSON 以外的任何文字。

输出格式：
{{
  "summary": "80–120 字",
  "highlights": ["20–40 字", "20–40 字", "20–40 字"],
  "audience": "20–40 字，可为空",
  "keywords": ["关键词1", "关键词2", "关键词3"]
}}

文章标题：
{title}

文章正文：
{body}
"""


# DH: 校验失败后追加的更严格提示词，用于第二次尝试。
SUMMARY_RETRY_SUFFIX = """

上一次输出不符合长度要求。请严格重写：
- 摘要必须在 80–120 字之间，不能超过 120 字；
- 三个看点每条不超过 40 字；
- 关键词 3–5 个。
只输出 JSON，不要解释。
"""


# 何君杰: 字段校验，不满足规格 3.7 的约束就视为失败
def _validate_payload(payload):
    if not isinstance(payload, dict):
        return False

    summary = payload.get('summary')
    if not isinstance(summary, str) or not summary.strip():
        return False
    # 何君杰: 严格校验 80~120 字
    summary_len = len(summary.strip())
    if not (80 <= summary_len <= 120):
        return False

    highlights = payload.get('highlights')
    if not isinstance(highlights, list) or len(highlights) != 3:
        return False
    for item in highlights:
        if not isinstance(item, str) or not item.strip():
            return False
        if len(item) > 40:
            return False

    audience = payload.get('audience', '')
    if not isinstance(audience, str):
        return False
    if audience and len(audience) > 40:
        return False

    keywords = payload.get('keywords')
    if not isinstance(keywords, list) or not (3 <= len(keywords) <= 5):
        return False
    for item in keywords:
        if not isinstance(item, str) or not item.strip():
            return False

    return True


# DH: 真实模型经常超出长度上限；先截到规格上限，再交给严格校验。
def _normalize_payload(payload):
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)

    summary = normalized.get('summary')
    if isinstance(summary, str):
        normalized['summary'] = summary.strip()[:120]

    highlights = normalized.get('highlights')
    if isinstance(highlights, list):
        normalized['highlights'] = [
            item.strip()[:40]
            for item in highlights
            if isinstance(item, str) and item.strip()
        ][:3]

    audience = normalized.get('audience')
    if isinstance(audience, str):
        normalized['audience'] = audience.strip()[:40]

    keywords = normalized.get('keywords')
    if isinstance(keywords, list):
        seen = set()
        cleaned = []
        for item in keywords:
            if not isinstance(item, str):
                continue
            text = item.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        normalized['keywords'] = cleaned[:5]

    return normalized


def _parse_ai_json(text):
    """何君杰: 从模型输出里解析 JSON；容忍 ```json 代码块包裹。"""
    text = (text or '').strip()
    if text.startswith('```'):
        # 去掉 ```json ... ``` 包裹
        lines = text.splitlines()
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines).strip()
    return json.loads(text)


def generate_ai_summary(article, force=False) -> bool:
    """生成导读，成功返回 True，失败返回 False，不抛异常。"""
    # 何君杰: 只处理已发布文章（规格 3.2）
    if article.status != 'p' or article.type != 'a':
        return False

    # 何君杰: done 且不强制时跳过，不调用 AI
    if article.ai_status == 'done' and not force:
        return True

    system_message = {
        'role': 'system',
        'content': '你是博客导读助手，只输出 JSON。',
    }
    prompt = SUMMARY_PROMPT.format(title=article.title, body=article.body)
    retry_prompt = (SUMMARY_PROMPT + SUMMARY_RETRY_SUFFIX).format(
        title=article.title, body=article.body
    )

    # DH: 最多两次：第一次正常提示词，字段不合格时用更严格提示词重试一次。
    last_reason = ''
    for attempt in range(2):
        user_prompt = prompt if attempt == 0 else retry_prompt
        messages = [system_message, {'role': 'user', 'content': user_prompt}]

        try:
            text = AIClient.chat(messages, temperature=0.2, max_tokens=800)
        except Exception as exc:
            # 何君杰: AI 失败不重试，直接 failed，不向外抛
            logger.warning(
                'AI 导读生成失败 article=%s: %s',
                article.pk,
                type(exc).__name__,
            )
            article.ai_status = 'failed'
            article.save(update_fields=['ai_status'])
            return False

        try:
            payload = _parse_ai_json(text)
        except Exception as exc:
            # 何君杰: JSON 解析失败视为 failed，不把半截内容写库
            logger.warning(
                'AI 导读生成失败 article=%s: %s',
                article.pk,
                type(exc).__name__,
            )
            article.ai_status = 'failed'
            article.save(update_fields=['ai_status'])
            return False

        # DH: 先归一化超长字段，再做严格校验。
        payload = _normalize_payload(payload)
        if _validate_payload(payload):
            # 何君杰: 成功写入 4 个内容字段 + 状态/时间/模型
            article.ai_summary = payload['summary'].strip()
            article.ai_highlights = [item.strip() for item in payload['highlights']]
            article.ai_audience = (payload.get('audience') or '').strip()
            article.ai_keywords = [item.strip() for item in payload['keywords']]
            article.ai_status = 'done'
            article.ai_generated_at = now()
            article.ai_model = getattr(settings, 'AI_MODEL', 'deepseek-chat')
            article.save(update_fields=[
                'ai_summary',
                'ai_highlights',
                'ai_audience',
                'ai_keywords',
                'ai_status',
                'ai_generated_at',
                'ai_model',
            ])
            return True

        last_reason = '字段校验失败'
        if attempt == 0:
            logger.info('AI 导读字段校验失败，重试一次 article=%s', article.pk)

    # DH: 两次都不合格才 failed，不把半截内容写库。
    logger.warning('AI 导读字段校验失败 article=%s: %s', article.pk, last_reason)
    article.ai_status = 'failed'
    article.save(update_fields=['ai_status'])
    return False
