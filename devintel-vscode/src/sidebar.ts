/**
 * DevIntelSidebarProvider — VS Code Webview sidebar that renders an
 * AI chat UI calling the DevIntel backend with SSE streaming.
 *
 * Supports:
 *  - Repository selection + streaming RAG chat
 *  - "Review File" trigger from the editor command
 *  - Auth state change notifications
 */

import * as vscode from "vscode";
import { DevIntelAuth } from "./auth";

export class DevIntelSidebarProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly _auth: DevIntelAuth
    ) { }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ): void {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };

        webviewView.webview.html = this._getHtml();

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async (msg) => {
            switch (msg.type) {
                case "ready":
                    await this._sendConfig();
                    break;

                case "chat": {
                    const { repoId, question, history } = msg;
                    await this._streamChat(webviewView.webview, repoId, question, history);
                    break;
                }

                case "getRepos": {
                    await this._sendRepos(webviewView.webview);
                    break;
                }

                case "setToken": {
                    const token = await vscode.window.showInputBox({
                        prompt: "Paste your DevIntel API token (JWT from app settings)",
                        password: true,
                        placeHolder: "eyJ...",
                    });
                    if (token) {
                        await this._auth.setToken(token);
                        await this._sendConfig();
                        webviewView.webview.postMessage({ type: "authUpdated" });
                    }
                    break;
                }
            }
        });
    }

    /** Called by extension.ts when auth changes externally */
    notifyAuthChanged(): void {
        if (this._view) {
            this._sendConfig();
        }
    }

    /** Called when user runs "DevIntel: Review Current File" command */
    async triggerFileReview(filePath: string, content: string, language: string): Promise<void> {
        if (!this._view) return;
        this._view.webview.postMessage({
            type: "reviewFile",
            filePath,
            content: content.slice(0, 8000), // limit context
            language,
        });
    }

    // ─── Private helpers ─────────────────────────────────────────────────────

    private async _sendConfig(): Promise<void> {
        if (!this._view) return;
        const token = await this._auth.getToken();
        const apiBaseUrl = this._auth.getApiBaseUrl();
        this._view.webview.postMessage({
            type: "config",
            apiBaseUrl,
            hasToken: !!token,
        });
    }

    private async _sendRepos(webview: vscode.Webview): Promise<void> {
        const token = await this._auth.getToken();
        const headers = await this._auth.buildHeaders();
        const apiBaseUrl = this._auth.getApiBaseUrl();

        try {
            const resp = await fetch(`${apiBaseUrl}/api/v1/repos`, { headers });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = (await resp.json()) as { repositories: { id: string; full_name: string; indexed_status: boolean }[] };
            webview.postMessage({ type: "repos", repositories: data.repositories || [] });
        } catch (e: unknown) {
            webview.postMessage({ type: "repos", repositories: [], error: e instanceof Error ? e.message : String(e) });
        }
    }

    private async _streamChat(
        webview: vscode.Webview,
        repoId: string,
        question: string,
        history: { role: string; content: string }[]
    ): Promise<void> {
        const headers = await this._auth.buildHeaders();
        const apiBaseUrl = this._auth.getApiBaseUrl();

        try {
            const resp = await fetch(`${apiBaseUrl}/api/v1/chat`, {
                method: "POST",
                headers,
                body: JSON.stringify({ repository_id: repoId, question, chat_history: history }),
            });

            if (!resp.ok || !resp.body) {
                webview.postMessage({ type: "chatError", message: `HTTP ${resp.status}` });
                return;
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() ?? "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.error) {
                            webview.postMessage({ type: "chatError", message: data.error });
                            return;
                        }
                        if (data.content) {
                            webview.postMessage({ type: "chatChunk", content: data.content });
                        }
                        if (data.done) {
                            webview.postMessage({
                                type: "chatDone",
                                costUsd: data.cost_usd,
                                tokenUsage: data.token_usage,
                            });
                        }
                    } catch {
                        // skip malformed SSE frames
                    }
                }
            }
        } catch (e: unknown) {
            webview.postMessage({ type: "chatError", message: e instanceof Error ? e.message : String(e) });
        }
    }

    private _getHtml(): string {
        return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DevIntel AI Chat</title>
  <style>
    :root {
      --radius: 6px;
      --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font);
      font-size: 13px;
      background: var(--vscode-sideBar-background);
      color: var(--vscode-foreground);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    /* ── Header ── */
    #header {
      padding: 10px 12px 8px;
      border-bottom: 1px solid var(--vscode-widget-border);
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    #header h1 {
      font-size: 13px;
      font-weight: 600;
      flex: 1;
    }
    #auth-btn {
      font-size: 11px;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: var(--radius);
      padding: 3px 8px;
      cursor: pointer;
    }
    #auth-btn:hover { opacity: 0.85; }

    /* ── Repo selector ── */
    #repo-bar {
      padding: 6px 12px;
      border-bottom: 1px solid var(--vscode-widget-border);
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }
    #repo-label { font-size: 11px; color: var(--vscode-descriptionForeground); }
    #repo-select {
      flex: 1;
      font-size: 12px;
      background: var(--vscode-dropdown-background);
      color: var(--vscode-dropdown-foreground);
      border: 1px solid var(--vscode-dropdown-border);
      border-radius: var(--radius);
      padding: 3px 6px;
      outline: none;
    }

    /* ── Messages ── */
    #messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .msg {
      max-width: 100%;
      padding: 8px 10px;
      border-radius: var(--radius);
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .msg.user {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      align-self: flex-end;
      max-width: 90%;
    }
    .msg.assistant {
      background: var(--vscode-editor-inactiveSelectionBackground);
      align-self: flex-start;
      max-width: 100%;
    }
    .msg .cost-tag {
      margin-top: 4px;
      font-size: 10px;
      color: var(--vscode-descriptionForeground);
    }
    .msg.error { background: var(--vscode-inputValidation-errorBackground); }

    /* ── No-auth / empty state ── */
    #empty-state {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 20px;
      text-align: center;
      color: var(--vscode-descriptionForeground);
    }
    #empty-state button {
      font-size: 12px;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: var(--radius);
      padding: 6px 14px;
      cursor: pointer;
    }
    #empty-state button:hover { opacity: 0.85; }

    /* ── Input bar ── */
    #input-bar {
      border-top: 1px solid var(--vscode-widget-border);
      padding: 8px 12px;
      display: flex;
      gap: 6px;
      flex-shrink: 0;
    }
    #user-input {
      flex: 1;
      font-family: var(--font);
      font-size: 12px;
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      border-radius: var(--radius);
      padding: 6px 8px;
      outline: none;
      resize: none;
      height: 32px;
      max-height: 80px;
      overflow-y: auto;
    }
    #user-input:focus { border-color: var(--vscode-focusBorder); }
    #send-btn {
      font-size: 16px;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: var(--radius);
      padding: 0 10px;
      cursor: pointer;
      flex-shrink: 0;
    }
    #send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    #send-btn:not(:disabled):hover { opacity: 0.85; }

    .spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid var(--vscode-foreground);
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>

<!-- Header -->
<div id="header">
  <h1>⚡ DevIntel AI</h1>
  <button id="auth-btn">Set Token</button>
</div>

<!-- Repo selector -->
<div id="repo-bar" style="display:none">
  <span id="repo-label">Repo:</span>
  <select id="repo-select"><option value="">Loading…</option></select>
</div>

<!-- Main area (messages or empty state) -->
<div id="main-area" style="display:flex;flex-direction:column;flex:1;overflow:hidden">
  <div id="empty-state">
    <div style="font-size:24px">🤖</div>
    <p>Connect your DevIntel API token to start chatting with your codebase.</p>
    <button onclick="vscode.postMessage({type:'setToken'})">Set API Token</button>
  </div>
  <div id="messages" style="display:none"></div>
</div>

<!-- Input bar -->
<div id="input-bar">
  <textarea id="user-input" rows="1" placeholder="Ask about your codebase…" disabled></textarea>
  <button id="send-btn" disabled>➤</button>
</div>

<script>
  const vscode = acquireVsCodeApi();

  let state = {
    apiBaseUrl: '',
    hasToken: false,
    repos: [],
    selectedRepoId: '',
    streaming: false,
    streamMsgEl: null,
  };

  // DOM refs
  const authBtn     = document.getElementById('auth-btn');
  const repoBar     = document.getElementById('repo-bar');
  const repoSelect  = document.getElementById('repo-select');
  const emptyState  = document.getElementById('empty-state');
  const messagesEl  = document.getElementById('messages');
  const userInput   = document.getElementById('user-input');
  const sendBtn     = document.getElementById('send-btn');

  authBtn.addEventListener('click', () => vscode.postMessage({ type: 'setToken' }));

  repoSelect.addEventListener('change', () => {
    state.selectedRepoId = repoSelect.value;
    updateInputState();
  });

  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // ── Message handling ──────────────────────────────────────────────────────
  window.addEventListener('message', ({ data }) => {
    switch (data.type) {
      case 'config':
        state.apiBaseUrl = data.apiBaseUrl;
        state.hasToken   = data.hasToken;
        applyConfig();
        break;

      case 'repos':
        state.repos = data.repositories || [];
        populateRepoSelector();
        break;

      case 'chatChunk':
        appendChunk(data.content);
        break;

      case 'chatDone':
        finaliseStream(data.costUsd, data.tokenUsage);
        break;

      case 'chatError':
        appendError(data.message);
        break;

      case 'authUpdated':
        applyConfig();
        break;

      case 'reviewFile':
        handleReviewFile(data.filePath, data.content, data.language);
        break;
    }
  });

  // ── Config ────────────────────────────────────────────────────────────────
  function applyConfig() {
    if (state.hasToken) {
      emptyState.style.display = 'none';
      messagesEl.style.display = 'flex';
      repoBar.style.display    = 'flex';
      vscode.postMessage({ type: 'getRepos' });
    } else {
      emptyState.style.display = 'flex';
      messagesEl.style.display = 'none';
      repoBar.style.display    = 'none';
    }
    updateInputState();
  }

  function populateRepoSelector() {
    const indexed = state.repos.filter(r => r.indexed_status);
    repoSelect.innerHTML = '';
    if (indexed.length === 0) {
      repoSelect.innerHTML = '<option value="">No indexed repos</option>';
    } else {
      indexed.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.textContent = r.full_name;
        repoSelect.appendChild(opt);
      });
      state.selectedRepoId = indexed[0].id;
    }
    updateInputState();
  }

  function updateInputState() {
    const ready = state.hasToken && state.selectedRepoId && !state.streaming;
    userInput.disabled = !ready;
    sendBtn.disabled   = !ready;
    userInput.placeholder = !state.hasToken
      ? 'Set API token first…'
      : !state.selectedRepoId
      ? 'Select an indexed repository…'
      : 'Ask about your codebase…';
  }

  // ── Chat ──────────────────────────────────────────────────────────────────
  function buildHistory() {
    return Array.from(messagesEl.querySelectorAll('.msg')).map(el => ({
      role: el.classList.contains('user') ? 'user' : 'assistant',
      content: el.dataset.raw || el.textContent || '',
    })).slice(-10);
  }

  function sendMessage() {
    const text = userInput.value.trim();
    if (!text || state.streaming || !state.selectedRepoId) return;

    appendUserMsg(text);
    userInput.value = '';
    state.streaming = true;
    sendBtn.innerHTML = '<span class="spinner"></span>';
    updateInputState();

    vscode.postMessage({
      type: 'chat',
      repoId: state.selectedRepoId,
      question: text,
      history: buildHistory(),
    });
  }

  function appendUserMsg(text) {
    const el = document.createElement('div');
    el.className = 'msg user';
    el.textContent = text;
    el.dataset.raw = text;
    messagesEl.appendChild(el);
    scrollBottom();
  }

  function appendChunk(chunk) {
    if (!state.streamMsgEl) {
      const el = document.createElement('div');
      el.className = 'msg assistant';
      messagesEl.appendChild(el);
      state.streamMsgEl = el;
    }
    state.streamMsgEl.dataset.raw = (state.streamMsgEl.dataset.raw || '') + chunk;
    state.streamMsgEl.textContent = state.streamMsgEl.dataset.raw;
    scrollBottom();
  }

  function finaliseStream(costUsd, tokenUsage) {
    if (state.streamMsgEl && costUsd != null) {
      const tag = document.createElement('div');
      tag.className = 'cost-tag';
      tag.textContent = '~$' + costUsd.toFixed(5) + ' · ' + (tokenUsage || 0) + ' tokens';
      state.streamMsgEl.appendChild(tag);
    }
    state.streamMsgEl = null;
    state.streaming = false;
    sendBtn.innerHTML = '➤';
    updateInputState();
    scrollBottom();
  }

  function appendError(message) {
    const el = document.createElement('div');
    el.className = 'msg error';
    el.textContent = '⚠ ' + message;
    messagesEl.appendChild(el);
    state.streamMsgEl = null;
    state.streaming = false;
    sendBtn.innerHTML = '➤';
    updateInputState();
    scrollBottom();
  }

  function handleReviewFile(filePath, content, language) {
    const question = 'Review this ' + language + ' file for bugs, security issues, and improvements:\\n\\nFile: ' + filePath + '\\n\\n\`\`\`' + language + '\\n' + content + '\\n\`\`\`';
    userInput.value = '';
    appendUserMsg('📄 Reviewing: ' + filePath.split(/[\\\\/]/).pop());
    state.streaming = true;
    sendBtn.innerHTML = '<span class="spinner"></span>';
    updateInputState();
    vscode.postMessage({
      type: 'chat',
      repoId: state.selectedRepoId,
      question,
      history: [],
    });
  }

  function scrollBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  vscode.postMessage({ type: 'ready' });
</script>
</body>
</html>`;
    }
}
