import { useState, useRef, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api } from '../../lib/axios';
import type { Repository } from '../../types/repository';
import type { ChatMessage } from '../../types/api';
import { Send, Loader2, Bot, User, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';

interface DisplayMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;
    const question = input.trim();
    setInput('');

    const userMsg: DisplayMessage = { role: 'user', content: question, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);

    const chatHistory: ChatMessage[] = messages.slice(-10).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    setIsStreaming(true);
    const assistantMsg: DisplayMessage = { role: 'assistant', content: '', timestamp: new Date() };
    setMessages((prev) => [...prev, assistantMsg]);

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
          body: JSON.stringify({
            repository_id: repository.id,
            question,
            chat_history: chatHistory,
            agent_type: agentType || null,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader');

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
              if (data.content) {
                fullContent += data.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { ...updated[updated.length - 1], content: fullContent };
                  return updated;
                });
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (error) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: 'Sorry, I encountered an error processing your request. Please try again.',
        };
        return updated;
      });
    } finally {
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
          <div className="flex flex-col items-center justify-center h-full text-center py-16">
            <Bot className="h-10 w-10 text-text-quaternary mb-4" />
            <h3 className="text-sm font-semibold text-text-primary mb-1">Chat with your code</h3>
            <p className="text-xs text-text-quaternary max-w-sm">
              Ask questions about {repository.repo_name} — architecture, patterns, bugs, or anything else. Powered by RAG semantic search.
            </p>
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
            <div className={clsx('max-w-[75%]', msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant')}>
              <div className="text-sm text-text-primary whitespace-pre-wrap leading-relaxed">
                {msg.content || (isStreaming && i === messages.length - 1 && (
                  <Loader2 className="h-4 w-4 animate-spin-slow text-text-quaternary" />
                ))}
              </div>
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
            onClick={handleSend}
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
