import type { UsageTrend } from '../../types/api';

interface UsageTrendChartProps {
  data: UsageTrend[];
}

export function UsageTrendChart({ data }: UsageTrendChartProps) {
  if (data.length === 0) {
    return (
      <div className="card p-5 flex flex-col items-center justify-center animate-slide-up">
        <div className="text-[10px] font-semibold text-text-quaternary uppercase tracking-widest mb-3">
          Usage Trend
        </div>
        <p className="text-xs text-text-quaternary">No usage data yet</p>
        <p className="text-[10px] text-text-quaternary mt-1">Start querying to see trends</p>
      </div>
    );
  }

  const maxQueries = Math.max(...data.map((d) => d.queries), 1);
  const chartHeight = 80;
  const chartWidth = 200;
  const padding = 4;

  // Build SVG path
  const points = data.map((d, i) => {
    const x = padding + (i / Math.max(data.length - 1, 1)) * (chartWidth - padding * 2);
    const y = chartHeight - padding - (d.queries / maxQueries) * (chartHeight - padding * 2);
    return { x, y };
  });

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${chartHeight} L ${points[0].x} ${chartHeight} Z`;

  const totalQueries = data.reduce((sum, d) => sum + d.queries, 0);

  return (
    <div className="card p-5 flex flex-col animate-slide-up">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">
          Usage Trend
        </div>
        <span className="text-xs font-medium text-text-tertiary">
          {totalQueries} total
        </span>
      </div>

      <div className="flex-1 flex items-end">
        <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-20" preserveAspectRatio="none">
          {/* Gradient */}
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          {/* Area fill */}
          <path d={areaPath} fill="url(#trendGradient)" />
          {/* Line */}
          <path d={linePath} fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          {/* Dots */}
          {points.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="2" fill="#6366f1" />
          ))}
        </svg>
      </div>

      <div className="flex justify-between mt-2 text-[10px] text-text-quaternary">
        <span>{data[0]?.date?.slice(5) ?? ''}</span>
        <span>{data[data.length - 1]?.date?.slice(5) ?? ''}</span>
      </div>
    </div>
  );
}
