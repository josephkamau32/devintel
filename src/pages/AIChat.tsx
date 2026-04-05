import { useState, useRef, useEffect, useCallback } from "react";
import { Send, GitBranch, Loader2, Trash2, ChevronDown, Check, Sparkles } from "lucide-react";
import { ChatMessage } from "@/components/shared/ChatMessage";
import { Loader } from "@/components/shared/Loader";
import { apiClient, API_BASE_URL } from "@/lib/api-client";
import type { ChatMessageData, Repository } from "@/lib/types";

const SUGGESTED_PROMPTS = [
  "Explain the overall architecture of this codebase",
  "Show me all the API endpoints and their purposes",
  "Find potential bugs or error handling issues",
  "Explain the data models and their relationships",
];

export default function AIChatPage() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [repoDropdownOpen, setRepoDropdownOpen] = useState(false);
  const [sessionCost, setSessionCost] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setRepoDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch user repos
  useEffect(() => {
    async function fetchRepos() {
      try {
        const data = await apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos');
        const repoList = data.repositories || [];
        setRepos(repoList);
        const indexed = repoList.find(r => r.indexed_status === true);
        if (indexed) setSelectedRepo(indexed);
      } catch (err) {
        console.error('Failed to fetch repos:', err);
      } finally {
        setLoadingRepos(false);
      }
    }
    fetchRepos();
  }, []);

  const handleSend = useCallback(async (question?: string) => {
    const text = (question ?? input).trim();
    if (!text || loading || !selectedRepo) return;

    const userMsg: ChatMessageData = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    // Build chat history from existing messages (last 10)
    const chatHistory = messages.slice(-10).map(m => ({
      role: m.role,
      content: m.content,
    }));

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          repository_id: selectedRepo.id,
          question: text,
          chat_history: chatHistory,
        }),
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let finalTokenUsage: number | undefined;
      let finalInputTokens: number | undefined;
      let finalOutputTokens: number | undefined;
      let finalCostUsd: number | undefined;
      let finalResponseTimeMs: number | undefined;

      const assistantMsgId = (Date.now() + 1).toString();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.error) throw new Error(data.error);

                if (data.content) {
                  fullContent += data.content;
                  setMessages((prev) => {
                    const existing = prev.find(m => m.id === assistantMsgId);
                    if (existing) {
                      return prev.map(m => m.id === assistantMsgId ? { ...m, content: fullContent } : m);
                    } else {
                      return [...prev, {
                        id: assistantMsgId,
                        role: 'assistant' as const,
                        content: fullContent,
                        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                      }];
                    }
                  });
                }

                if (data.done && data.token_usage !== undefined) {
                  finalTokenUsage = data.token_usage;
                  finalInputTokens = data.input_tokens;
                  finalOutputTokens = data.output_tokens;
                  finalCostUsd = data.cost_usd;
                  finalResponseTimeMs = data.response_time_ms;
                }
              } catch (e) {
                // Skip malformed SSE lines
              }
            }
          }
        }
      }

      // Attach token/time/cost stats to the final message
      if (finalTokenUsage !== undefined) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                ...m,
                tokenUsage: finalTokenUsage,
                inputTokens: finalInputTokens,
                outputTokens: finalOutputTokens,
                costUsd: finalCostUsd,
                responseTimeMs: finalResponseTimeMs,
              }
              : m
          )
        );
        if (finalCostUsd) {
          setSessionCost((prev) => prev + finalCostUsd!);
        }
      }

      if (!fullContent) {
        setMessages((prev) => [...prev, {
          id: assistantMsgId,
          role: 'assistant',
          content: 'Sorry, I could not generate a response. Please make sure the repository is indexed.',
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        }]);
      }
    } catch (err: unknown) {
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Something went wrong. Please try again.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, loading, selectedRepo, messages]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSelectRepo = (repo: Repository) => {
    setSelectedRepo(repo);
    setMessages([]);
    setRepoDropdownOpen(false);
  };

  const indexedRepos = repos.filter(r => r.indexed_status === true);
  const nonIndexedRepos = repos.filter(r => !r.indexed_status);

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      {/* Header with repo selector */}
      <div className="flex items-center gap-3 border-b border-border pb-4">
        <GitBranch className="h-4 w-4 text-muted-foreground shrink-0" />
        <span className="text-sm text-muted-foreground shrink-0">Repository:</span>

        {loadingRepos ? (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : repos.length === 0 ? (
          <span className="text-sm text-destructive">No repositories connected</span>
        ) : (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setRepoDropdownOpen(v => !v)}
              className="flex items-center gap-2 h-8 rounded-md border border-input bg-accent px-3 text-sm text-foreground outline-none hover:border-primary transition-colors"
            >
              <span className="truncate max-w-[200px]">
                {selectedRepo ? selectedRepo.full_name : "Select a repository"}
              </span>
              <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform shrink-0 ${repoDropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {repoDropdownOpen && (
              <div className="absolute top-full mt-1 left-0 z-50 w-72 rounded-lg border border-border bg-card shadow-lg overflow-hidden animate-slide-up">
                {indexedRepos.length > 0 && (
                  <>
                    <p className="px-3 pt-2.5 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Indexed
                    </p>
                    {indexedRepos.map(r => (
                      <button
                        key={r.id}
                        onClick={() => handleSelectRepo(r)}
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent transition-colors"
                      >
                        <span className="flex-1 truncate text-card-foreground">{r.full_name}</span>
                        {selectedRepo?.id === r.id && <Check className="h-3.5 w-3.5 text-primary shrink-0" />}
                      </button>
                    ))}
                  </>
                )}
                {nonIndexedRepos.length > 0 && (
                  <>
                    <p className="px-3 pt-2.5 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground border-t border-border mt-1">
                      Not Indexed
                    </p>
                    {nonIndexedRepos.map(r => (
                      <button
                        key={r.id}
                        disabled
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left opacity-40 cursor-not-allowed"
                      >
                        <span className="flex-1 truncate text-card-foreground">{r.full_name}</span>
                      </button>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Session cost */}
        {sessionCost > 0 && (
          <span className="flex items-center gap-1 rounded-md border border-border bg-card px-2 py-1 text-xs text-muted-foreground">
            <span className="text-emerald-400 font-medium">~${sessionCost.toFixed(5)}</span>
            <span>this session</span>
          </span>
        )}

        {/* Clear conversation */}
        {messages.length > 0 && (
          <button
            onClick={() => { setMessages([]); setSessionCost(0); }}
            title="Clear conversation"
            className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto py-6 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-6">
            <div>
              <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-3 mx-auto">
                <Sparkles className="h-7 w-7 text-primary" />
              </div>
              <p className="text-base font-semibold text-foreground">Ask anything about your code</p>
              <p className="mt-1 text-sm text-muted-foreground max-w-sm">
                {selectedRepo
                  ? `Chatting with ${selectedRepo.full_name}`
                  : 'Select an indexed repository above to get started.'}
              </p>
            </div>

            {/* Suggested prompts */}
            {selectedRepo && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg w-full px-4">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="rounded-xl border border-border bg-card px-4 py-3 text-left text-sm text-card-foreground hover:border-primary/50 hover:bg-accent transition-colors leading-snug"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-foreground shrink-0">
              <div className="h-4 w-4" />
            </div>
            <div className="rounded-xl border border-border bg-card px-4 py-3">
              <Loader />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border pt-4">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={selectedRepo ? "Ask about your codebase..." : "Select a repository first..."}
            disabled={!selectedRepo || loading}
            className="h-10 flex-1 rounded-lg border border-input bg-accent px-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors disabled:opacity-50"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading || !selectedRepo}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground disabled:opacity-50 transition-opacity hover:opacity-90"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-muted-foreground">
          Press <kbd className="rounded border border-border px-1 py-0.5 font-mono text-[9px]">Enter</kbd> to send
        </p>
      </div>
    </div>
  );
}
