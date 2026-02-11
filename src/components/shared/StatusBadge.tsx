interface StatusBadgeProps {
  status: string;
  variant?: 'success' | 'warning' | 'error' | 'default' | 'primary';
}

const variantClasses: Record<string, string> = {
  success: 'bg-success/10 text-success border-success/20',
  warning: 'bg-warning/10 text-warning border-warning/20',
  error: 'bg-destructive/10 text-destructive border-destructive/20',
  primary: 'bg-primary/10 text-primary border-primary/20',
  default: 'bg-muted text-muted-foreground border-border',
};

export function StatusBadge({ status, variant = 'default' }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${variantClasses[variant]}`}>
      {variant === 'success' && <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-success" />}
      {variant === 'warning' && <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-warning animate-pulse-slow" />}
      {status}
    </span>
  );
}
