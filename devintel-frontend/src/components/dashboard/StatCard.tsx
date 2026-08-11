import { clsx } from 'clsx';

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  variant?: 'default' | 'warning' | 'error' | 'success';
  format?: 'number' | 'compact';
}

function formatCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function StatCard({ label, value, icon, variant = 'default', format = 'number' }: StatCardProps) {
  const iconColors = {
    default: 'text-text-quaternary',
    warning: 'text-status-warning',
    error: 'text-status-error',
    success: 'text-status-success',
  };

  const valueBgs = {
    default: '',
    warning: 'text-status-warning',
    error: 'text-status-error',
    success: 'text-status-success',
  };

  return (
    <div className="stat-card group animate-slide-up">
      <div className="flex items-center gap-2 mb-1">
        <span className={clsx('transition-colors', iconColors[variant])}>{icon}</span>
        <span className="text-xs font-medium text-text-quaternary uppercase tracking-wider truncate">
          {label}
        </span>
      </div>
      <div className={clsx('text-stat-sm font-bold', valueBgs[variant] || 'text-text-primary')}>
        {format === 'compact' ? formatCompact(value) : value.toLocaleString()}
      </div>
    </div>
  );
}
