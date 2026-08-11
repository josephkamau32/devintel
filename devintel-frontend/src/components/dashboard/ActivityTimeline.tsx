import type { AnalyticsDashboard } from '../../types/api';
import type { Repository } from '../../types/repository';
import { Clock, MessageSquareText, FolderGit2, Database } from 'lucide-react';

interface ActivityTimelineProps {
  analytics: AnalyticsDashboard | undefined;
  repositories: Repository[];
}

interface TimelineEvent {
  icon: React.ReactNode;
  title: string;
  detail: string;
  time: string;
  color: string;
}

function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function ActivityTimeline({ analytics, repositories }: ActivityTimelineProps) {
  const events: TimelineEvent[] = [];

  // Add last active event
  if (analytics?.last_active_at) {
    events.push({
      icon: <MessageSquareText className="h-3.5 w-3.5" />,
      title: 'Last AI query',
      detail: `${analytics.total_queries} total queries`,
      time: formatRelativeTime(analytics.last_active_at),
      color: 'bg-brand-600',
    });
  }

  // Add repo activity
  repositories.forEach((repo) => {
    const isIndexed = repo.indexing_status === 'completed' || repo.indexing_status === 'complete';
    const isIndexing = ['pending', 'indexing', 'cloning', 'chunking', 'embedding'].includes(repo.indexing_status);

    if (isIndexing) {
      events.push({
        icon: <Database className="h-3.5 w-3.5" />,
        title: `Indexing ${repo.repo_name}`,
        detail: repo.indexing_status,
        time: 'In progress',
        color: 'bg-status-info',
      });
    } else if (isIndexed) {
      events.push({
        icon: <FolderGit2 className="h-3.5 w-3.5" />,
        title: `${repo.repo_name} indexed`,
        detail: repo.full_name,
        time: 'Completed',
        color: 'bg-status-success',
      });
    }
  });

  // Add top repo usage
  analytics?.top_repositories?.slice(0, 3).forEach((usage) => {
    events.push({
      icon: <Clock className="h-3.5 w-3.5" />,
      title: usage.repo_name,
      detail: `${usage.queries} queries`,
      time: '',
      color: 'bg-surface-5',
    });
  });

  return (
    <div className="card h-full flex flex-col">
      <div className="px-5 py-3 border-b border-border">
        <h3 className="text-sm font-semibold text-text-primary">Recent Activity</h3>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <Clock className="h-6 w-6 text-text-quaternary mb-3" />
            <p className="text-sm text-text-tertiary">No activity yet</p>
            <p className="text-xs text-text-quaternary mt-1">
              Connect and index a repository to get started
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {events.map((event, i) => (
              <div key={i} className="flex gap-3 animate-slide-up" style={{ animationDelay: `${i * 40}ms` }}>
                <div className={`flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-full ${event.color} text-white`}>
                  {event.icon}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text-primary truncate">{event.title}</p>
                  <p className="text-xs text-text-quaternary truncate">{event.detail}</p>
                </div>
                {event.time && (
                  <span className="text-[10px] text-text-quaternary flex-shrink-0 mt-0.5">{event.time}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
