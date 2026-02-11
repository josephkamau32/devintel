import { useState, useRef, useEffect } from "react";
import { Send, GitBranch } from "lucide-react";
import { ChatMessage } from "@/components/shared/ChatMessage";
import { Loader } from "@/components/shared/Loader";
import { mockChatMessages, api, type ChatMessageData } from "@/lib/mock-data";

export default function AIChatPage() {
  const [messages, setMessages] = useState<ChatMessageData[]>(mockChatMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessageData = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const response = await api.sendChatMessage(userMsg.content);
    setMessages((prev) => [...prev, response]);
    setLoading(false);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border pb-4">
        <GitBranch className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Connected Repository:</span>
        <span className="text-sm font-medium text-foreground">acme/api-gateway</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto py-6 space-y-4">
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
            placeholder="Ask about your codebase..."
            className="h-10 flex-1 rounded-lg border border-input bg-accent px-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground disabled:opacity-50 transition-opacity hover:opacity-90"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
