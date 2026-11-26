import { useState, useRef, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../../lib/axios';
import type { Repository } from '../../types/repository';
import type { ChatMessage } from '../../types/api';
import { Send, Loader2, Bot, User, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { MarkdownMessage } from '../../components/chat/MarkdownMessage';

interface DisplayMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isError?: boolean;
  failedQuestion?: string;
}

export function ChatTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentType, setAgentType] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const isIndexed = repository.indexing_status === 'completed' || repository.indexing_status === 'complete';
  const isSampleRepo = repository.full_name === 'josephkamau32/devintel' || repository.full_name === 'devintel/devintel-core';

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (questionOverride?: string) => {
    const question = (questionOverride || input).trim();
    if (!question || isStreaming) return;
    if (!questionOverride) {
      setInput('');
    }

    const userMsg: DisplayMessage = { role: 'user', content: question, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);

    const chatHistory: ChatMessage[] = messages.slice(-10).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    setIsStreaming(true);
    const assistantMsg: DisplayMessage = { role: 'assistant', content: '', timestamp: new Date() };
    setMessages((prev) => [...prev, assistantMsg]);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    try {
      const response = await fetch(
        `${api.defaults.baseURL}/chat/${repository.id}/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${(await import('../../store/authStore')).useAuthStore.getState().accessToken}`,
          },
          credentials: 'include',
          signal: controller.signal,
          body: JSON.stringify({
            repository_id: repository.id,
            question,
            chat_history: chatHistory,
            agent_type: agentType || null,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No readable stream from server');

      let fullContent = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'error' || data.error) {
                const errorMsg = data.message || data.error || 'An error occurred while processing your request.';
                throw new Error(errorMsg);
              }
              if (data.content) {
                fullContent += data.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { ...updated[updated.length - 1], content: fullContent };
                  return updated;
                });
              }
            } catch (err: unknown) {
              const errMessage = err instanceof Error ? err.message : String(err);
              if (errMessage.includes('error') || errMessage.includes('Error') || errMessage.includes('failed') || errMessage.includes('processing')) {
                throw err;
              }
            }
          }
        }
      }
    } catch (error: unknown) {
      const isAbort = error instanceof Error && error.name === 'AbortError';
      const errorMessage = isAbort
        ? 'Response timed out. The AI model may be overloaded. Click Retry to try again.'
        : (error instanceof Error ? error.message : 'Sorry, I encountered an error processing your request. Please try again.');

      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        if (lastIdx >= 0) {
          updated[lastIdx] = {
            ...updated[lastIdx],
            content: errorMessage,
            isError: true,
            failedQuestion: question,
          };
        }
        return updated;
      });
    } finally {
      clearTimeout(timeoutId);
      setIsStreaming(false);
    }
  };

  if (!isIndexed) {
    return (
      <div className="card p-10 text-center animate-fade-in">
        <Bot className="h-8 w-8 text-text-quaternary mx-auto mb-4" />
        <h2 className="text-h3 text-text-primary mb-2">Index required</h2>
        <p className="text-body text-text-tertiary max-w-md mx-auto">
          Index this repository to start chatting with your code using RAG-powered AI.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-220px)] animate-fade-in">
      {/* Agent type selector */}
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="h-3.5 w-3.5 text-text-quaternary" />
        <select
          value={agentType}
          onChange={(e) => setAgentType(e.target.value)}
          className="text-xs bg-surface-3 border border-border rounded-md px-2 py-1 text-text-secondary outline-none focus:border-brand-500"
        >
          <option value="">General Agent</option>
          <option value="architect">Architect</option>
          <option value="security">Security</option>
          <option value="performance">Performance</option>
          <option value="test_engineer">Test Engineer</option>
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <Bot className="h-10 w-10 text-text-quaternary mb-4" />
            <h3 className="text-sm font-semibold text-text-primary mb-1">Chat with your code</h3>
            <p className="text-xs text-text-quaternary max-w-sm mb-6">
              Ask questions about {repository.repo_name} — architecture, patterns, bugs, or anything else. Powered by RAG semantic search.
            </p>
            {isSampleRepo && (
              <div className="w-full max-w-md space-y-2 text-left animate-fade-in">
                <p className="text-[11px] font-medium text-text-quaternary uppercase tracking-wider text-center mb-2">
                  Suggested questions for indexed modules
                </p>
                {[
                  'How does the AI orchestrator handle model timeouts and fallback routing?',
                  'How does the CodeHealthService analyze complexity and maintainability?',
                  'What database models are defined for repositories and embeddings?',
                ].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    className="w-full text-left p-3 rounded-lg text-xs bg-surface-2 hover:bg-surface-3 border border-border hover:border-brand-500/50 text-text-secondary hover:text-text-primary transition-all flex items-center justify-between group"
                  >
                    <span>{q}</span>
                    <Sparkles className="h-3.5 w-3.5 text-text-quaternary group-hover:text-brand-400 transition-colors flex-shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={clsx('flex gap-3 animate-slide-up', msg.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 flex items-start">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600">
                  <Bot className="h-3.5 w-3.5 text-white" />
                </div>
              </div>
            )}
            <div className={clsx('max-w-[75%]', msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant', msg.isError && 'border border-danger-500/30 bg-danger-500/5')}>
              {msg.content ? (
                msg.role === 'assistant' && !msg.isError ? (
                  <MarkdownMessage content={msg.content} />
                ) : (
                  <div className={clsx('text-sm whitespace-pre-wrap leading-relaxed', msg.isError ? 'text-danger-300' : 'text-text-primary')}>
                    {msg.content}
                  </div>
                )
              ) : isStreaming && i === messages.length - 1 ? (
                <div className="flex items-center gap-2 text-xs text-text-quaternary py-0.5">
                  <Loader2 className="h-4 w-4 animate-spin-slow text-brand-400" />
                  <span>Thinking...</span>
                </div>
              ) : null}

              {msg.isError && msg.failedQuestion && !isStreaming && (
                <div className="mt-2.5 pt-2 border-t border-border/40 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-danger-400">
                    <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                    <span>Generation failed</span>
                  </div>
                  <button
                    onClick={() => handleSend(msg.failedQuestion)}
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-400 hover:text-brand-300 bg-brand-500/10 hover:bg-brand-500/20 px-2.5 py-1 rounded-md transition-colors"
                  >
                    <RefreshCw className="h-3 w-3" />
                    Retry
                  </button>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="flex-shrink-0 flex items-start">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-surface-4">
                  <User className="h-3.5 w-3.5 text-text-tertiary" />
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border pt-4">
        <div className="flex items-end gap-3 bg-surface-2 border border-border rounded-xl p-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={`Ask about ${repository.repo_name}…`}
            className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-quaternary outline-none resize-none min-h-[36px] max-h-[120px]"
            rows={1}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isStreaming}
            className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-30 text-white transition-colors flex-shrink-0"
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin-slow" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
