/**
 * AI 站内问答前端组件。
 *
 * 文章页：右下角悬浮入口 + 正文划词浮标 + 右侧抽屉。
 * 独立页：/ai/ask/ 的问答表单。
 *
 * 原生 DOM + fetch，不依赖 Alpine；模型回答与来源文字一律用 textContent 渲染。
 */

const ARTICLE_PATH_RE = /\/article\/\d{4}\/\d{1,2}\/\d{1,2}\/(\d+)\.html/;
const MIN_SELECTED_TEXT = 5;
const MAX_SELECTED_TEXT = 500;
const MAX_HISTORY = 3;

const state = {
  articleId: null,
  selectedText: '',
  pendingSelectionText: '',
  selectionClickPending: false,
  history: [],
  loading: false,
  lastAttempt: null,
  conversationId: 0,
};

const boundAskPages = new WeakSet();

let initToken = 0;
let globalListenersReady = false;

function getCookie(name) {
  const prefix = `${name}=`;
  const cookies = document.cookie ? document.cookie.split(';') : [];
  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(prefix)) {
      return decodeURIComponent(trimmed.slice(prefix.length));
    }
  }
  return '';
}

function extractArticleId() {
  const match = ARTICLE_PATH_RE.exec(window.location.pathname);
  return match ? match[1] : null;
}

function isSafeUrl(url) {
  return (
    typeof url === 'string' &&
    (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/'))
  );
}

function ensureStyles() {
  if (document.getElementById('ai-qa-styles')) return;

  const style = document.createElement('style');
  style.id = 'ai-qa-styles';
  style.textContent = `
#ai-qa-root {
  position: fixed;
  inset: 0;
  z-index: 70;
  pointer-events: none;
}
#ai-qa-root > * {
  pointer-events: auto;
}
#ai-qa-root [data-ai-qa-entry] {
  position: fixed;
  right: 24px;
  bottom: 96px;
  z-index: 10;
}
#ai-qa-root [data-ai-qa-selection] {
  position: fixed;
  z-index: 20;
  transform: translate(-50%, -100%);
}
#ai-qa-root [data-ai-qa-selection][hidden] {
  display: none !important;
}
#ai-qa-drawer {
  position: fixed;
  inset: 0;
  z-index: 30;
  pointer-events: none;
}
#ai-qa-drawer .ai-qa-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
}
#ai-qa-drawer .ai-qa-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 400px;
  max-width: 100%;
  height: 100%;
  transform: translateX(100%);
  transition: transform 0.25s ease;
}
#ai-qa-drawer.ai-qa-open {
  pointer-events: auto;
}
#ai-qa-drawer.ai-qa-open .ai-qa-backdrop {
  opacity: 1;
  pointer-events: auto;
}
#ai-qa-drawer.ai-qa-open .ai-qa-panel {
  transform: translateX(0);
}
.ai-qa-messages {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.ai-qa-message {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.ai-qa-message-user {
  align-items: flex-end;
}
.ai-qa-message-ai {
  align-items: flex-start;
}
.ai-qa-bubble {
  max-width: 100%;
  border-radius: 0.75rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.55;
  word-break: break-word;
}
.ai-qa-answer {
  white-space: pre-wrap;
}
#ai-qa-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}
#ai-qa-status.ai-qa-status-error {
  color: #dc2626;
}
#ai-qa-selected-chip[hidden] {
  display: none !important;
}
@media (max-width: 640px) {
  #ai-qa-root [data-ai-qa-entry] {
    right: 16px;
    bottom: 88px;
  }
  #ai-qa-drawer .ai-qa-panel {
    width: 100%;
  }
}
`;
  document.head.appendChild(style);
}

function updateSendState() {
  const send = document.getElementById('ai-qa-send');
  const input = document.getElementById('ai-qa-input');
  if (!send || !input) return;
  send.disabled = state.loading || input.value.trim() === '';
}

function updateChip() {
  const chip = document.getElementById('ai-qa-selected-chip');
  if (!chip) return;

  const textElement = chip.querySelector('.ai-qa-chip-text');
  if (!state.selectedText) {
    chip.hidden = true;
    if (textElement) textElement.textContent = '';
    return;
  }

  chip.hidden = false;
  if (textElement) {
    const text = state.selectedText;
    textElement.textContent =
      text.length > 80 ? `${text.slice(0, 80)}…` : text;
  }
}

function setStatus(text, retryHandler, isError) {
  const status = document.getElementById('ai-qa-status');
  if (!status) return;

  status.replaceChildren();
  status.classList.toggle('ai-qa-status-error', Boolean(isError));

  if (text) {
    const message = document.createElement('span');
    message.textContent = text;
    status.appendChild(message);
  }

  if (typeof retryHandler === 'function') {
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.setAttribute('data-ai-qa-retry', '');
    retry.className =
      'rounded border border-border bg-card px-2 py-0.5 text-xs font-medium text-primary transition-colors hover:bg-secondary';
    retry.textContent = '重试';
    retry.addEventListener('click', retryHandler);
    status.appendChild(retry);
  }
}

function createSourceCard(citation) {
  const isComment = citation.type === 'comment';

  const card = document.createElement('div');
  card.className =
    'rounded-lg border border-border bg-card p-2.5 text-xs text-foreground';

  const header = document.createElement('div');
  header.className = 'flex flex-wrap items-center gap-1.5';

  const badge = document.createElement('span');
  badge.className =
    'shrink-0 rounded bg-secondary px-1.5 py-0.5 font-medium text-muted-foreground';
  badge.textContent = isComment ? '[评论观点]' : '[文章]';
  header.appendChild(badge);

  const title = document.createElement('span');
  title.className = 'font-medium';
  title.textContent =
    typeof citation.title === 'string' && citation.title
      ? citation.title
      : '未命名来源';
  header.appendChild(title);
  card.appendChild(header);

  if (typeof citation.snippet === 'string' && citation.snippet) {
    const snippet = document.createElement('p');
    snippet.className = 'mt-1.5 text-muted-foreground';
    snippet.textContent = citation.snippet;
    card.appendChild(snippet);
  }

  if (isComment && typeof citation.author === 'string' && citation.author) {
    const author = document.createElement('p');
    author.className = 'mt-1 text-muted-foreground';
    author.textContent = `作者：${citation.author}`;
    card.appendChild(author);
  }

  if (isSafeUrl(citation.url)) {
    const link = document.createElement('a');
    link.className = 'mt-1.5 inline-flex text-primary hover:underline';
    link.href = citation.url;
    link.textContent = isComment ? '查看评论' : '查看原文';
    card.appendChild(link);
  }

  return card;
}

function appendQuestion(question) {
  const messages = document.getElementById('ai-qa-messages');
  if (!messages) return;

  const row = document.createElement('div');
  row.className = 'ai-qa-message ai-qa-message-user';

  const bubble = document.createElement('div');
  bubble.className = 'ai-qa-bubble bg-primary text-primary-foreground';
  bubble.textContent = question;
  row.appendChild(bubble);

  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

function appendAnswer(answer, citations, meta) {
  const messages = document.getElementById('ai-qa-messages');
  if (!messages) return;

  const row = document.createElement('div');
  row.className = 'ai-qa-message ai-qa-message-ai';

  const bubble = document.createElement('div');
  bubble.className = 'ai-qa-bubble ai-qa-answer bg-secondary text-foreground';
  bubble.textContent = answer;
  row.appendChild(bubble);

  if (Array.isArray(citations) && citations.length > 0) {
    const sources = document.createElement('div');
    sources.className = 'mt-1 flex w-full flex-col gap-2';

    for (const citation of citations) {
      if (citation && typeof citation === 'object') {
        sources.appendChild(createSourceCard(citation));
      }
    }

    if (sources.childElementCount > 0) row.appendChild(sources);
  }

  if (meta && meta.cached === true) {
    const cached = document.createElement('span');
    cached.className =
      'inline-flex rounded bg-secondary px-1.5 py-0.5 text-xs text-muted-foreground';
    cached.textContent = '来自缓存';
    row.appendChild(cached);
  }

  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

function handleRequestError(status) {
  if (status === 400) {
    setStatus('请求参数不正确，请修改后重试。', null, true);
    return;
  }
  if (status === 429) {
    setStatus('提问太频繁，请稍后再试。', retryLastRequest, true);
    return;
  }
  if (status === 503) {
    setStatus('AI 服务暂时不可用，请稍后再试。', retryLastRequest, true);
    return;
  }
  setStatus('网络异常，请稍后重试。', retryLastRequest, true);
}

function retryLastRequest() {
  if (state.loading) return;
  const attempt = state.lastAttempt;
  if (!attempt) return;
  setStatus('', null, false);
  sendQuestion(attempt.question);
}

async function sendQuestion(question) {
  const trimmed = String(question || '').trim();
  if (!trimmed || state.loading) return;

  const conversationId = state.conversationId;
  const csrfToken = getCookie('csrftoken');
  if (!csrfToken) {
    setStatus('页面已过期，请刷新后重试', null, true);
    return;
  }

  const comments = document.getElementById('ai-qa-include-comments');
  const includeComments = comments ? comments.checked : true;
  const payload = {
    question: trimmed,
    selected_text: state.selectedText || '',
    article_id: state.articleId ? Number(state.articleId) : null,
    include_comments: includeComments,
    history: state.history.slice(-MAX_HISTORY).map((item) => ({
      question: item.question,
      answer: item.answer,
    })),
  };

  state.loading = true;
  state.lastAttempt = { question: trimmed };

  const input = document.getElementById('ai-qa-input');
  if (input) input.value = '';
  updateSendState();
  setStatus('正在检索站内资料…', null, false);

  try {
    const response = await fetch('/ai/ask/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      credentials: 'same-origin',
      body: JSON.stringify(payload),
    });

    if (conversationId !== state.conversationId) return;

    if (!response.ok) {
      handleRequestError(response.status);
      return;
    }

    let data;
    try {
      data = await response.json();
    } catch (error) {
      handleRequestError(0);
      return;
    }

    if (conversationId !== state.conversationId) return;

    const answer = typeof data.answer === 'string' ? data.answer : '';
    appendQuestion(trimmed);
    appendAnswer(answer, data.citations, data.meta);
    state.history.push({ question: trimmed, answer });
    state.history = state.history.slice(-MAX_HISTORY);
    setStatus('', null, false);
  } catch (error) {
    if (conversationId !== state.conversationId) return;
    handleRequestError(0);
  } finally {
    if (conversationId === state.conversationId) {
      state.loading = false;
      updateSendState();
    }
  }
}

function handleSubmit(event) {
  event.preventDefault();
  const input = document.getElementById('ai-qa-input');
  if (!input) return;

  const question = input.value.trim();
  if (!question) {
    updateSendState();
    return;
  }
  sendQuestion(question);
}

function clearConversation() {
  state.conversationId += 1;
  state.history = [];
  state.selectedText = '';
  state.pendingSelectionText = '';
  state.lastAttempt = null;
  state.loading = false;

  const messages = document.getElementById('ai-qa-messages');
  if (messages) messages.replaceChildren();

  const status = document.getElementById('ai-qa-status');
  if (status) {
    status.replaceChildren();
    status.classList.remove('ai-qa-status-error');
  }

  const input = document.getElementById('ai-qa-input');
  if (input) input.value = '';

  updateChip();
  updateSendState();
}

function openDrawer(options = {}) {
  const drawer = document.getElementById('ai-qa-drawer');
  if (!drawer) return;

  const selectedText =
    typeof options.selectedText === 'string'
      ? options.selectedText.slice(0, MAX_SELECTED_TEXT)
      : '';
  state.selectedText = selectedText;
  updateChip();

  const input = document.getElementById('ai-qa-input');
  if (input) {
    if (options.prefill && input.value.trim() === '') {
      input.value = options.prefill;
    }
    updateSendState();
  }

  drawer.classList.add('ai-qa-open');
  drawer.setAttribute('aria-hidden', 'false');

  window.setTimeout(() => {
    if (input) input.focus();
  }, 250);
}

function closeDrawer() {
  const drawer = document.getElementById('ai-qa-drawer');
  if (!drawer) return;

  drawer.classList.remove('ai-qa-open');
  drawer.setAttribute('aria-hidden', 'true');
  clearConversation();
}

function isInsideArticle(selection) {
  if (!selection.rangeCount) return false;
  const range = selection.getRangeAt(0);
  let node = range.commonAncestorContainer;
  if (node.nodeType !== Node.ELEMENT_NODE) node = node.parentElement;
  return Boolean(node && node.closest('.entry-content .article'));
}

function showSelectionButton(text, rect) {
  const button = document.querySelector(
    '#ai-qa-root [data-ai-qa-selection]',
  );
  if (!button) return;

  state.pendingSelectionText = text;
  button.hidden = false;

  const halfWidth = (button.offsetWidth || 64) / 2 + 8;
  const left = Math.min(
    Math.max(rect.left + rect.width / 2, halfWidth),
    window.innerWidth - halfWidth,
  );

  let top = rect.top - 8;
  let transform = 'translate(-50%, -100%)';
  if (top < 48) {
    top = rect.bottom + 8;
    transform = 'translate(-50%, 0)';
  }

  button.style.left = `${Math.round(left)}px`;
  button.style.top = `${Math.round(top)}px`;
  button.style.transform = transform;
}

function hideSelectionButton(clearPending = true) {
  const button = document.querySelector(
    '#ai-qa-root [data-ai-qa-selection]',
  );
  if (button) button.hidden = true;
  state.selectionClickPending = false;
  if (clearPending) state.pendingSelectionText = '';
}

function handleSelectionEvent(event) {
  if (!document.getElementById('ai-qa-root')) return;
  if (event.target instanceof Element && event.target.closest('#ai-qa-root')) {
    return;
  }

  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    hideSelectionButton(true);
    return;
  }

  const rawText = selection.toString().trim();
  if (!rawText) {
    hideSelectionButton(true);
    return;
  }

  const insideArticle =
    isInsideArticle(selection) ||
    (event.target instanceof Element &&
      Boolean(event.target.closest('.entry-content .article')));
  if (!insideArticle) {
    hideSelectionButton(true);
    return;
  }

  if (rawText.length < MIN_SELECTED_TEXT) {
    hideSelectionButton(true);
    return;
  }

  const text = rawText.slice(0, MAX_SELECTED_TEXT);
  const range = selection.getRangeAt(0);
  let rect = range.getBoundingClientRect();

  if ((!rect || (rect.width === 0 && rect.height === 0)) && range.getClientRects().length > 0) {
    rect = range.getClientRects()[0];
  }
  if ((!rect || (rect.width === 0 && rect.height === 0)) && event.target instanceof Element) {
    rect = event.target.getBoundingClientRect();
  }
  if (!rect) return;

  showSelectionButton(text, rect);
}

function installGlobalListeners() {
  if (globalListenersReady) return;
  globalListenersReady = true;

  document.addEventListener('mouseup', handleSelectionEvent);
  document.addEventListener('keyup', handleSelectionEvent);

  document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    if (!selection || !selection.toString().trim()) {
      // 点击浮标时浏览器可能先清空选区；等 click 处理完再决定是否隐藏。
      if (state.selectionClickPending) return;
      hideSelectionButton(false);
    }
  });

  document.addEventListener('mousedown', (event) => {
    const button = document.querySelector(
      '#ai-qa-root [data-ai-qa-selection]',
    );
    const pressedSelectionButton =
      button && event.target instanceof Node && button.contains(event.target);
    state.selectionClickPending = Boolean(pressedSelectionButton);
    if (pressedSelectionButton) return;
    hideSelectionButton(true);
  });

  window.addEventListener(
    'scroll',
    () => hideSelectionButton(true),
    { capture: true, passive: true },
  );

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    hideSelectionButton(true);
    const drawer = document.getElementById('ai-qa-drawer');
    if (drawer && drawer.classList.contains('ai-qa-open')) closeDrawer();
  });
}

function bindArticleUi(root) {
  const entry = root.querySelector('[data-ai-qa-entry]');
  const selectionButton = root.querySelector('[data-ai-qa-selection]');
  const closeButton = root.querySelector('#ai-qa-close');
  const backdrop = root.querySelector('[data-ai-qa-backdrop]');
  const chipRemove = root.querySelector('[data-ai-qa-chip-remove]');
  const form = root.querySelector('#ai-qa-form');
  const input = root.querySelector('#ai-qa-input');
  const comments = root.querySelector('#ai-qa-include-comments');

  if (entry) {
    entry.addEventListener('click', () => {
      hideSelectionButton(true);
      state.selectedText = '';
      updateChip();
      const inputElement = document.getElementById('ai-qa-input');
      if (inputElement) inputElement.value = '';
      openDrawer();
    });
  }

  if (selectionButton) {
    // 防止按下浮标时浏览器清空选区。
    selectionButton.addEventListener('mousedown', (event) => {
      event.preventDefault();
    });
    selectionButton.addEventListener('click', () => {
      const selectedText = state.pendingSelectionText;
      hideSelectionButton(true);
      if (!selectedText) return;
      openDrawer({ selectedText, prefill: '解释这段内容' });
    });
  }

  if (closeButton) closeButton.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);

  if (chipRemove) {
    chipRemove.addEventListener('click', () => {
      state.selectedText = '';
      updateChip();
      const inputElement = document.getElementById('ai-qa-input');
      if (inputElement) inputElement.focus();
    });
  }

  if (form) form.addEventListener('submit', handleSubmit);
  if (input) input.addEventListener('input', updateSendState);
  if (comments) comments.addEventListener('change', updateSendState);

  updateChip();
  updateSendState();
}

function injectArticleUi() {
  if (document.getElementById('ai-qa-root')) return;

  const root = document.createElement('div');
  root.id = 'ai-qa-root';
  root.innerHTML = `
    <button type="button" data-ai-qa-entry
            class="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-lg transition-opacity hover:opacity-90"
            aria-haspopup="dialog" aria-controls="ai-qa-drawer">问 AI</button>
    <button type="button" data-ai-qa-selection hidden
            class="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow-lg">问 AI</button>
    <div id="ai-qa-drawer" aria-hidden="true">
      <div class="ai-qa-backdrop" data-ai-qa-backdrop></div>
      <section class="ai-qa-panel flex h-full flex-col border-l border-border bg-card text-foreground shadow-2xl"
               role="dialog" aria-modal="true" aria-labelledby="ai-qa-title">
        <header class="flex shrink-0 items-center justify-between border-b border-border px-4 py-3">
          <h2 id="ai-qa-title" class="text-base font-bold text-foreground">AI 站内问答</h2>
          <button type="button" id="ai-qa-close"
                  class="rounded-md px-2 py-1 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  aria-label="关闭">关闭</button>
        </header>
        <div id="ai-qa-selected-chip" hidden
             class="mx-4 mt-3 flex shrink-0 items-start gap-2 rounded-lg border border-border bg-secondary px-3 py-2 text-xs text-muted-foreground">
          <span class="ai-qa-chip-text flex-1 break-words"></span>
          <button type="button" data-ai-qa-chip-remove
                  class="shrink-0 font-medium text-primary hover:underline">删除</button>
        </div>
        <div id="ai-qa-messages" class="ai-qa-messages flex-1 overflow-y-auto px-4 py-4"
             aria-live="polite"></div>
        <div id="ai-qa-status" class="min-h-[1.5rem] shrink-0 px-4 pb-1 text-xs text-muted-foreground"
             role="status" aria-live="polite"></div>
        <form id="ai-qa-form" class="shrink-0 border-t border-border px-4 py-3" novalidate>
          <label for="ai-qa-input" class="sr-only">输入你的问题</label>
          <textarea id="ai-qa-input" rows="2" maxlength="200" placeholder="输入你的问题…"
                    class="w-full resize-none rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"></textarea>
          <div class="mt-2 flex items-center justify-between gap-3">
            <label for="ai-qa-include-comments"
                   class="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
              <input type="checkbox" id="ai-qa-include-comments" checked
                     class="size-4 rounded border-border text-primary focus:ring-primary">
              包含评论
            </label>
            <button type="submit" id="ai-qa-send" disabled
                    class="rounded-lg bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50">发送</button>
          </div>
        </form>
      </section>
    </div>
  `;

  document.body.appendChild(root);
  bindArticleUi(root);
}

async function initArticlePage(articleId, token) {
  state.articleId = articleId;

  let status;
  try {
    const response = await fetch(
      `/ai/status/?article_id=${encodeURIComponent(articleId)}`,
      { credentials: 'same-origin' },
    );
    if (!response.ok) return;
    status = await response.json();
  } catch (error) {
    return;
  }

  if (token !== initToken) return;
  if (extractArticleId() !== articleId) return;
  if (!status || status.enabled !== true || status.article_type !== 'a') return;
  if (document.getElementById('ai-qa-root')) return;

  injectArticleUi();
}

function initAskPage(root) {
  if (root.getAttribute('data-ai-enabled') !== 'true') return;
  if (boundAskPages.has(root)) return;
  boundAskPages.add(root);

  state.articleId = null;
  state.selectedText = '';
  state.history = [];
  state.loading = false;
  state.lastAttempt = null;

  const form = root.querySelector('#ai-qa-form');
  const input = root.querySelector('#ai-qa-input');
  const comments = root.querySelector('#ai-qa-include-comments');
  const examples = root.querySelectorAll('[data-ai-example]');

  if (form) form.addEventListener('submit', handleSubmit);
  if (input) input.addEventListener('input', updateSendState);
  if (comments) comments.addEventListener('change', updateSendState);

  examples.forEach((button) => {
    button.addEventListener('click', () => {
      if (!input) return;
      const question =
        button.getAttribute('data-ai-example') || button.textContent || '';
      input.value = question.trim();
      input.focus();
      updateSendState();
    });
  });

  updateSendState();
}

function removeInjectedUi() {
  const root = document.getElementById('ai-qa-root');
  if (root) root.remove();
}

function resetState() {
  state.conversationId += 1;
  state.articleId = null;
  state.selectedText = '';
  state.pendingSelectionText = '';
  state.selectionClickPending = false;
  state.history = [];
  state.loading = false;
  state.lastAttempt = null;
}

function init() {
  initToken += 1;
  const token = initToken;

  ensureStyles();
  removeInjectedUi();
  hideSelectionButton(true);

  const articleId = extractArticleId();
  if (articleId) {
    resetState();
    initArticlePage(articleId, token);
    return;
  }

  const askPage = document.getElementById('ai-ask-page');
  if (askPage) {
    if (boundAskPages.has(askPage)) return;
    resetState();
    initAskPage(askPage);
    return;
  }

  resetState();
}

installGlobalListeners();

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
  init();
}

document.addEventListener('htmx:afterSwap', () => {
  // afterSwap 触发时 htmx 可能尚未更新地址栏，延后一拍再按新 URL 初始化。
  window.setTimeout(init, 0);
});
