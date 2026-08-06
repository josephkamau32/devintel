import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message?: string;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  if (!message) return null;

  return (
    <div
      role="alert"
      className="flex items-center gap-2 rounded-lg border border-status-error/20 bg-status-error-muted px-3.5 py-2.5 text-sm text-status-error"
    >
      <AlertCircle className="h-4 w-4 shrink-0" />
      <p>{message}</p>
    </div>
  );
}
