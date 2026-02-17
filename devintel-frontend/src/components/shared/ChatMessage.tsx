import { Bot, User } from "lucide-react";
import { CodeBlock } from "./CodeBlock";
import type { ChatMessageData } from "@/lib/mock-data";

interface ChatMessageProps {
  message: ChatMessageData;
}

function parseContent(content: string) {
  const parts: { type: "text" | "code"; content: string; language?: string }[] = [];
  const regex = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: content.slice(lastIndex, match.index) });
    }
    parts.push({ type: "code", content: match[2].trim(), language: match[1] });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({ type: "text", content: content.slice(lastIndex) });
  }

  return parts;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const parts = parseContent(message.content);

  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-primary/10 text-primary"
            : "bg-accent text-foreground"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-card border border-border text-card-foreground"
        }`}
      >
        {parts.map((part, i) =>
          part.type === "code" ? (
            <CodeBlock key={i} code={part.content} language={part.language} />
          ) : (
            <span key={i} className="whitespace-pre-wrap">
              {part.content}
            </span>
          )
        )}
        <div className={`mt-1 text-[10px] ${isUser ? "text-primary-foreground/60" : "text-muted-foreground"}`}>
          {message.timestamp}
        </div>
      </div>
    </div>
  );
}
