

interface EngHealthScoreProps {
  score: number | null;
  repoCount: number;
}

function getScoreColor(score: number): string {
  if (score >= 90) return '#06b6d4'; // excellent - cyan
  if (score >= 70) return '#22c55e'; // good - green
  if (score >= 40) return '#f59e0b'; // warning - amber
  return '#ef4444'; // critical - red
}

function getScoreLabel(score: number): string {
  if (score >= 90) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 40) return 'Fair';
  return 'Critical';
}

export function EngHealthScore({ score, repoCount }: EngHealthScoreProps) {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = score !== null ? circumference - (score / 100) * circumference : circumference;
  const color = score !== null ? getScoreColor(score) : '#52525b';

  return (
    <div className="card p-5 flex flex-col items-center justify-center animate-slide-up">
      <div className="text-[10px] font-semibold text-text-quaternary uppercase tracking-widest mb-3">
        Engineering Health
      </div>

      <div className="relative w-28 h-28">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          {/* Track */}
          <circle cx="50" cy="50" r={radius} className="score-ring-track" />
          {/* Value */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            className="score-ring-value"
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ '--score-offset': offset } as React.CSSProperties}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {score !== null ? (
            <>
              <span className="text-2xl font-bold text-text-primary">{score}</span>
              <span className="text-[10px] font-medium" style={{ color }}>
                {getScoreLabel(score)}
              </span>
            </>
          ) : (
            <span className="text-xs text-text-quaternary text-center px-2">No data</span>
          )}
        </div>
      </div>

      <p className="text-xs text-text-quaternary mt-3">
        {repoCount > 0
          ? `Across ${repoCount} ${repoCount === 1 ? 'repository' : 'repositories'}`
          : 'Analyze a repository to see scores'}
      </p>
    </div>
  );
}
