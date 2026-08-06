import { ButtonHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
  icon?: ReactNode;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  icon,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const base =
    'inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/25 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 disabled:opacity-40 disabled:cursor-not-allowed select-none';

  const variants: Record<string, string> = {
    primary:
      'bg-brand-600 text-white hover:bg-brand-500 active:bg-brand-700 shadow-subtle hover:shadow-medium',
    secondary:
      'bg-surface-3 text-text-primary border border-border-medium hover:bg-surface-4 hover:border-border-strong active:bg-surface-5',
    ghost:
      'text-text-secondary hover:text-text-primary hover:bg-surface-3 active:bg-surface-4',
    danger:
      'bg-status-error text-white hover:bg-red-500 active:bg-red-700',
    outline:
      'border border-border-medium text-text-secondary hover:text-text-primary hover:bg-surface-3 hover:border-border-strong',
  };

  const sizes: Record<string, string> = {
    sm: 'rounded-md px-3 py-1.5 text-xs',
    md: 'rounded-lg px-4 py-2 text-sm',
    lg: 'rounded-lg px-5 py-2.5 text-sm',
  };

  return (
    <button
      className={clsx(
        base,
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin-slow" />
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
}
