import { useState, useRef, useEffect } from "react";
import { Send, GitBranch, Loader2 } from "lucide-react";
import { ChatMessage } from "@/components/shared/ChatMessage";
import { Loader } from "@/components/shared/Loader";
import { apiClient, API_BASE_URL } from "@/lib/api-client";
import type { ChatMessageData, Repository } from "@/lib/types";

export default function AIChatPage() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Fetch user repos
  useEffect(() => {
    async function fetchRepos() {
      try {
        const data = await apiClient.get<{ repositories: Repository[]; total: number }>('/api/v1/repos');
        const repoList = data.repositories || [];
        setRepos(repoList);
        // Auto-select first indexed repo
        const indexed = repoList.find(r => r.indexed_status === 'completed');
        if (indexed) setSelectedRepo(indexed);
      } catch (err) {
        console.error('Failed to fetch repos:', err);
      } finally {
        setLoadingRepos(false);
      }
    }
    fetchRepos();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading || !selectedRepo) return;

    const userMsg: ChatMessageData = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
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
          question: userMsg.content,
        }),
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      // Handle SSE streaming
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

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
                if (data.error) {
                  throw new Error(data.error);
                }
                if (data.content) {
                  fullContent += data.content;
                  // Update message in real-time
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
              } catch (e) {
                // Skip malformed SSE lines
              }
            }
          }
        }
      }

      // If no streaming response came through, add a fallback
      if (!fullContent) {
        setMessages((prev) => [...prev, {
          id: assistantMsgId,
          role: 'assistant',
          content: 'Sorry, I could not generate a response. Please make sure the repository is indexed.',
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        }]);
      }
    } catch (err: any) {
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err.message || 'Something went wrong. Please try again.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      {/* Header with repo selector */}
      <div className="flex items-center gap-3 border-b border-border pb-4">
        <GitBranch className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Repository:</span>
        {loadingRepos ? (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : repos.length === 0 ? (
          <span className="text-sm text-destructive">No repositories connected</span>
        ) : (
          <select
            value={selectedRepo?.id || ''}
            onChange={(e) => {
              const repo = repos.find(r => r.id === e.target.value);
              setSelectedRepo(repo || null);
              setMessages([]);
            }}
            className="h-8 rounded-md border border-input bg-accent px-2 text-sm text-foreground outline-none focus:border-primary transition-colors"
          >
            <option value="" disabled>Select a repository</option>
            {repos.map(r => (
              <option key={r.id} value={r.id} disabled={r.indexed_status !== 'completed'}>
                {r.full_name} {r.indexed_status !== 'completed' ? '(not indexed)' : ''}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto py-6 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
              <GitBranch className="h-6 w-6 text-primary" />
            </div>
            <p className="text-sm font-medium text-foreground">Ask anything about your code</p>
            <p className="mt-1 text-xs text-muted-foreground max-w-sm">
              {selectedRepo
                ? `Chat with ${selectedRepo.full_name}. Ask about architecture, patterns, bugs, or any code-related question.`
                : 'Select an indexed repository above to get started.'}
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-foreground">
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
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={selectedRepo ? "Ask about your codebase..." : "Select a repository first..."}
            disabled={!selectedRepo}
            className="h-10 flex-1 rounded-lg border border-input bg-accent px-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading || !selectedRepo}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground disabled:opacity-50 transition-opacity hover:opacity-90"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
