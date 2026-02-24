import { useState, useRef, useEffect } from "react";
import { Send, GitBranch, Loader2, Database, AlertCircle, Trash2 } from "lucide-react";
import { ChatMessage } from "@/components/shared/ChatMessage";
import { Button } from "@/components/ui/button";
import { useRepositories } from "@/hooks/useRepositories";
import { useChat } from "@/hooks/useChat";

export default function AIChatPage() {
  const { repos, loading: reposLoading } = useRepositories();
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);

  const {
    messages,
    loading,
    streamingContent,
    error,
    loadHistory,
    sendMessage,
    clearHistory
  } = useChat(selectedRepoId || undefined);

  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Initialize selected repo
  useEffect(() => {
    if (repos.length > 0 && !selectedRepoId) {
      setSelectedRepoId(repos[0].id);
    }
  }, [repos, selectedRepoId]);

  // Load history when repo changes
  useEffect(() => {
    if (selectedRepoId) {
      loadHistory(selectedRepoId);
    }
  }, [selectedRepoId, loadHistory]);

  // Scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading || !selectedRepoId) return;
    const question = input.trim();
    setInput("");
    await sendMessage(question);
  };

  const selectedRepo = repos.find(r => r.id === selectedRepoId);

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      {/* Header & Repo Selector */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-foreground">
            {selectedRepo ? selectedRepo.repo_name : "Select a repository"}
          </span>
          {selectedRepo?.indexed_status && (
            <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-bold text-success uppercase tracking-wider">
              <Database className="h-2.5 w-2.5" /> Indexed
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedRepoId || ""}
            onChange={(e) => setSelectedRepoId(e.target.value)}
            className="h-9 rounded-md border border-input bg-card px-3 py-1 text-sm outline-none focus:ring-1 focus:ring-primary min-w-[200px]"
          >
            {repos.map(r => (
              <option key={r.id} value={r.id}>{r.repo_name}</option>
            ))}
            {repos.length === 0 && <option value="">No repos connected</option>}
          </select>
          <Button
            variant="ghost"
            size="icon"
            onClick={clearHistory}
            className="text-muted-foreground hover:text-destructive"
            title="Clear context"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-auto px-1 py-2 space-y-6">
        {messages.length === 0 && !loading && !streamingContent && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
            <div className="p-4 rounded-full bg-primary/5">
              <GitBranch className="h-12 w-12 text-primary/40" />
            </div>
            <div>
              <p className="text-lg font-medium">Chat with your code</p>
              <p className="text-sm text-card-foreground">Ask questions about architecture, logic, or dependencies.</p>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <ChatMessage key={idx} message={{
            ...msg,
            id: idx.toString(),
            timestamp: msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : undefined
          }} />
        ))}

        {streamingContent && (
          <ChatMessage message={{
            id: "streaming",
            role: "assistant",
            content: streamingContent,
          }} />
        )}

        {loading && !streamingContent && (
          <div className="flex gap-3 animate-in fade-in duration-300">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
            <div className="rounded-2xl border border-border bg-card px-4 py-3 shadow-sm italic text-muted-foreground text-sm">
              Analyzing repository context...
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-destructive/5 border border-destructive/20 text-destructive text-sm">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <div ref={bottomRef} className="h-4" />
      </div>

      {/* Input Area */}
      <div className="pt-2">
        <div className="relative group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={loading || !selectedRepoId}
            placeholder={selectedRepoId ? "Ask about your codebase..." : "Select a repository to start chatting"}
            className="h-12 w-full rounded-xl border border-input bg-card pl-4 pr-12 text-sm text-foreground shadow-sm placeholder:text-muted-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading || !selectedRepoId}
            className="absolute right-2 top-1/2 -translate-y-1/2 flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-muted-foreground uppercase tracking-widest font-medium">
          Powered by DevIntel RAG Engine
        </p>
      </div>
    </div>
  );
}
