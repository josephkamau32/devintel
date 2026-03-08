import { useState, useRef, useEffect, useCallback } from "react";
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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea as user types
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [input]);

  // Agent mode state
  const [isAgentMode, setIsAgentMode] = useState(false);
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);

  // Draft State
  const [agentDraft, setAgentDraft] = useState<{
    pr_title: string;
    pr_body: string;
    branch_name: string;
    commit_message: string;
    file_changes: { path: string; content: string }[];
  } | null>(null);

  // Execution State
  const [isExecuting, setIsExecuting] = useState(false);
  const [agentResult, setAgentResult] = useState<{ pr_url: string; branch_name: string } | null>(null);

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
  }, [messages, streamingContent, loading, agentLoading, agentDraft, agentResult, agentError]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || loading || agentLoading || isExecuting || !selectedRepoId) return;
    const question = input.trim();
    setInput("");
    // Reset textarea height after clearing
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Clear previous agent results if starting a new request
    setAgentError(null);
    setAgentResult(null);
    setAgentDraft(null);

    if (isAgentMode) {
      setAgentLoading(true);
      try {
        const { apiClient } = await import('@/lib/api-client');
        type DraftResponse = { draft: typeof agentDraft };
        const response = await apiClient.draftAgentAction(selectedRepoId, question) as DraftResponse;
        setAgentDraft(response.draft ?? null);
      } catch (err: unknown) {
        const _err = err as { response?: { data?: { detail?: string } } };
        setAgentError(_err.response?.data?.detail || "Failed to generate PR draft. Check server logs.");
      } finally {
        setAgentLoading(false);
      }
    } else {
      await sendMessage(question);
    }
  }, [input, loading, agentLoading, isExecuting, selectedRepoId, isAgentMode, sendMessage]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift); allow Shift+Enter for newlines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const executeDraft = async () => {
    if (!agentDraft || !selectedRepoId || isExecuting) return;

    setIsExecuting(true);
    setAgentError(null);
    try {
      const { apiClient } = await import('@/lib/api-client');
      type ExecuteResponse = { pr_url: string; branch_name: string };
      const response = await apiClient.executeAgentAction(selectedRepoId, agentDraft) as ExecuteResponse;
      setAgentResult({
        pr_url: response.pr_url,
        branch_name: response.branch_name,
      });
      setAgentDraft(null); // Clear draft after success
    } catch (err: unknown) {
      const _err = err as { response?: { data?: { detail?: string } } };
      setAgentError(_err.response?.data?.detail || "Failed to execute PR on GitHub.");
    } finally {
      setIsExecuting(false);
    }
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
          {/* Agent Mode Toggle */}
          <div className="flex items-center gap-2 mr-2">
            <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
              Agent Mode
            </span>
            <button
              onClick={() => setIsAgentMode(!isAgentMode)}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center justify-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${isAgentMode ? 'bg-primary' : 'bg-muted'
                }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-background shadow ring-0 transition duration-200 ease-in-out ${isAgentMode ? 'translate-x-4' : 'translate-x-0'
                  }`}
              />
            </button>
          </div>

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

        {agentLoading && (
          <div className="flex gap-3 animate-in fade-in duration-300">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
            <div className="rounded-2xl border border-border bg-card px-4 py-3 shadow-sm italic text-muted-foreground text-sm">
              Drafting Proposed Changes...
            </div>
          </div>
        )}

        {/* Agent error shown inline in message flow */}
        {agentError && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-destructive/5 border border-destructive/20 text-destructive text-sm animate-in fade-in duration-300">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <p>{agentError}</p>
          </div>
        )}

        {agentDraft && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
              <GitBranch className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-none border border-border bg-card p-4 shadow-sm w-full max-w-2xl text-sm">
              <h3 className="font-semibold text-lg mb-2">Review Proposed Changes</h3>
              <div className="bg-muted p-3 flex flex-col gap-2 rounded-lg mb-4 text-xs font-mono">
                <div><strong className="text-foreground">Branch:</strong> {agentDraft.branch_name}</div>
                <div><strong className="text-foreground">Commit:</strong> {agentDraft.commit_message}</div>
                <div><strong className="text-foreground">PR Title:</strong> {agentDraft.pr_title}</div>
                <div className="mt-1"><strong className="text-foreground">PR Body:</strong><br />{agentDraft.pr_body}</div>
              </div>
              <div className="mb-4">
                <strong className="text-foreground mb-2 block text-xs">Files Changed ({agentDraft.file_changes.length}):</strong>
                <ul className="list-disc list-inside text-xs text-muted-foreground ml-2">
                  {agentDraft.file_changes.map(fc => <li key={fc.path}>{fc.path}</li>)}
                </ul>
              </div>
              <div className="flex items-center gap-3">
                <Button onClick={executeDraft} disabled={isExecuting} className="gap-2">
                  {isExecuting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Execute PR on GitHub
                </Button>
                <Button variant="outline" onClick={() => setAgentDraft(null)} disabled={isExecuting}>
                  Discard
                </Button>
              </div>
            </div>
          </div>
        )}

        {agentResult && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-success/10 border border-success/20 text-success text-sm">
            <GitBranch className="h-4 w-4 shrink-0" />
            <div>
              <p className="font-semibold">Pull Request Created Successfully!</p>
              <a
                href={agentResult.pr_url}
                target="_blank"
                rel="noreferrer"
                className="underline underline-offset-2 hover:text-success/80 mt-1 block"
              >
                View PR on GitHub
              </a>
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
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || agentLoading || isExecuting || !selectedRepoId}
            placeholder={selectedRepoId ? (isAgentMode ? "Describe a change to implement..." : "Ask about your codebase...") : "Select a repository to start"}
            aria-label="Chat input"
            className="w-full resize-none rounded-xl border border-input bg-card pl-4 pr-12 py-3 text-sm text-foreground shadow-sm placeholder:text-muted-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all disabled:opacity-50 overflow-hidden leading-relaxed"
            style={{ minHeight: '48px', maxHeight: '200px' }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading || agentLoading || isExecuting || !selectedRepoId}
            aria-label="Send message"
            className="absolute right-2 bottom-2 flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
          >
            {(loading || agentLoading) ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-muted-foreground uppercase tracking-widest font-medium">
          {isAgentMode ? "Agent Mode · Enter to draft · Shift+Enter for newline" : "Powered by DevIntel RAG Engine · Shift+Enter for newline"}
        </p>
      </div>
    </div>
  );
}
