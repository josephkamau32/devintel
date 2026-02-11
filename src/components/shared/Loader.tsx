export function Loader({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-1.5 ${className}`}>
      <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
      <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
      <span className="h-2 w-2 rounded-full bg-primary animate-bounce" />
    </div>
  );
}
