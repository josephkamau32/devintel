import { type LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: { value: string; positive: boolean };
  delay?: number;
}

export function StatCard({ title, value, subtitle, icon: Icon, trend, delay = 0 }: StatCardProps) {
  return (
    <div 
      className="glass-card rounded-xl p-5 relative overflow-hidden group animate-fade-in"
      style={{ animationDelay: `${delay}ms`, opacity: 0, animationFillMode: 'forwards' }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
      
      <div className="relative z-10 flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="mt-1 text-3xl font-bold text-foreground drop-shadow-[0_0_10px_hsl(var(--primary)/20)] tracking-tight">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
          {trend && (
            <p className={`mt-2 text-xs font-semibold px-2 py-0.5 inline-block rounded-full border ${trend.positive ? "text-success border-success/20 bg-success/10 shadow-[0_0_10px_-2px_hsl(var(--success)/0.2)]" : "text-destructive border-destructive/20 bg-destructive/10 shadow-[0_0_10px_-2px_hsl(var(--destructive)/0.2)]"}`}>
              {trend.positive ? "↑" : "↓"} {trend.value}
            </p>
          )}
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_-3px_hsl(var(--primary)/0.2)] transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:bg-primary/20 group-hover:shadow-[0_0_20px_-3px_hsl(var(--primary)/0.4)]">
          <Icon className="h-6 w-6 drop-shadow-[0_0_5px_currentColor]" />
        </div>
      </div>
    </div>
  );
}
