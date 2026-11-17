# DH: AI 问答 HTTP 接口：状态查询 + JSON 问答（校验/限流/缓存/CSRF）
import json
from hashlib import sha256

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from blog.ai_qa import answer_question
from blog.models import Article
from djangoblog.ai import AIClientError

# DH: 对外错误文案固定，不向上游/客户端泄露内部细节
ERROR_400 = {'error': '请求参数不正确'}
ERROR_429 = {'error': '提问太频繁，请稍后再试'}
ERROR_503 = {'error': 'AI 服务暂时不可用，请稍后再试'}

# DH: 限流 10 次/分钟；首轮回答缓存 1 小时
RATE_LIMIT = 10
RATE_WINDOW = 60
CACHE_TTL = 3600

MAX_QUESTION_LEN = 200
MAX_SELECTED_TEXT_LEN = 500
MAX_HISTORY_ROUNDS = 3


def _ai_enabled():
    # DH: 开关与 Key 必须同时具备；缺一即 fail closed
    return bool(settings.AI_ENABLED and settings.AI_API_KEY)


def _validate_payload(payload):
    # DH: 校验通过返回规范化后的字段，失败返回 None（统一 400）
    question = payload.get('question')
    if not isinstance(question, str):
        return None
    stripped_question = question.strip()
    if not stripped_question or len(stripped_question) > MAX_QUESTION_LEN:
        return None

    selected_text = payload.get('selected_text', '')
    if not isinstance(selected_text, str):
        return None
    if len(selected_text) > MAX_SELECTED_TEXT_LEN:
        return None

    article_id = payload.get('article_id')
    if article_id is not None:
        # DH: bool 是 int 的子类，必须显式排除
        if isinstance(article_id, bool) or not isinstance(article_id, int):
            return None
        if not Article.objects.filter(
            pk=article_id, status='p', type='a'
        ).exists():
            return None

    include_comments = payload.get('include_comments', True)
    if not isinstance(include_comments, bool):
        return None

    history = payload.get('history', [])
    if not isinstance(history, list) or len(history) > MAX_HISTORY_ROUNDS:
        return None
    for item in history:
        if not isinstance(item, dict):
            return None
        if not isinstance(item.get('question'), str):
            return None
        if not isinstance(item.get('answer'), str):
            return None

    return {
        'question': question,
        'selected_text': selected_text,
        'article_id': article_id,
        'include_comments': include_comments,
        'history': history,
    }


def _get_published_article_type(article_id):
    # DH: 只暴露已发布文章的 type；缺失/非法/草稿一律 None
    try:
        article_id = int(article_id)
    except (TypeError, ValueError):
        return None
    return (
        Article.objects.filter(pk=article_id, status='p')
        .values_list('type', flat=True)
        .first()
    )


@require_GET
def ai_status(request):
    # DH: 前端据此判断是否注入入口；不返回模型名/Base URL/Key
    enabled = _ai_enabled()
    article_type = None
    if enabled:
        article_type = _get_published_article_type(
            request.GET.get('article_id')
        )
    return JsonResponse({'enabled': enabled, 'article_type': article_type})


@require_http_methods(['GET', 'POST'])
def ai_ask(request):
    if request.method == 'GET':
        return render(
            request, 'ai/ask.html', {'ai_enabled': _ai_enabled()}
        )

    # DH: AI 关闭或缺 Key 时直接 503，不解析请求体
    if not _ai_enabled():
        return JsonResponse(ERROR_503, status=503)

    try:
        payload = json.loads(request.body)
    except (TypeError, ValueError):
        return JsonResponse(ERROR_400, status=400)
    if not isinstance(payload, dict):
        return JsonResponse(ERROR_400, status=400)

    data = _validate_payload(payload)
    if data is None:
        return JsonResponse(ERROR_400, status=400)

    question = data['question']
    selected_text = data['selected_text']
    article_id = data['article_id']
    include_comments = data['include_comments']
    history = data['history']

    # DH: 先限流再读缓存，避免缓存命中绕过频率限制
    ip = request.META.get('REMOTE_ADDR', '')
    rate_key = f'ai_qa_rate:{ip}'
    cache.add(rate_key, 0, RATE_WINDOW)
    try:
        count = cache.incr(rate_key)
    except ValueError:
        # DH: 计数键恰好过期时重新开始计数
        cache.set(rate_key, 1, RATE_WINDOW)
        count = 1
    if count > RATE_LIMIT:
        return JsonResponse(ERROR_429, status=429)

    # DH: 仅首轮（无 history）读缓存；多轮不读不写
    cache_key = None
    if not history:
        raw = (
            f"{question}|{selected_text}|"
            f"{article_id or ''}|{int(include_comments)}"
        )
        digest = sha256(raw.encode('utf-8')).hexdigest()
        cache_key = f"ai_qa:{digest}:{settings.AI_INDEX_VERSION}"
        cached = cache.get(cache_key)
        if cached is not None:
            return JsonResponse({
                'answer': cached.get('answer', ''),
                'citations': cached.get('citations', []),
                'meta': {
                    'model': settings.AI_MODEL,
                    'cached': True,
                },
            })

    try:
        result = answer_question(
            question,
            selected_text=selected_text,
            article_id=article_id,
            include_comments=include_comments,
            history=history,
            base_url=request.build_absolute_uri('/'),
        )
    except AIClientError:
        # DH: 上游异常统一 503，不泄露异常文本
        return JsonResponse(ERROR_503, status=503)

    answer = result.get('answer', '')
    citations = result.get('citations', [])
    if cache_key is not None:
        cache.set(
            cache_key,
            {'answer': answer, 'citations': citations},
            CACHE_TTL,
        )

    return JsonResponse({
        'answer': answer,
        'citations': citations,
        'meta': {
            'model': settings.AI_MODEL,
            'cached': False,
        },
    })
