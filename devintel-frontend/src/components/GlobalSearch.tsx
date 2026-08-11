import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FolderGit2, ArrowRight, FileCode2, Loader2, X, Sparkles, BarChart3, Network } from 'lucide-react';
import { useSemanticSearch } from '../hooks/useAPI';
import type { Repository } from '../types/repository';

interface GlobalSearchProps {
  onClose: () => void;
  repositories: Repository[];
}

export function GlobalSearch({ onClose, repositories }: GlobalSearchProps) {
  const [query, setQuery] = useState('');
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const semanticSearch = useSemanticSearch();

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleEsc(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === overlayRef.current) onClose();
    },
    [onClose],
  );

  // Filter repos by query
  const filteredRepos = query.trim()
    ? repositories.filter(
        (r) =>
          r.repo_name.toLowerCase().includes(query.toLowerCase()) ||
          r.full_name.toLowerCase().includes(query.toLowerCase()),
      )
    : repositories.slice(0, 5);

  // Quick actions
  const quickActions = [
    { label: 'AI Insights', icon: Sparkles, path: '/insights' },
    { label: 'Analytics', icon: BarChart3, path: '/analytics' },
    { label: 'Architecture', icon: Network, path: '/repositories' },
  ];

  const handleSemanticSearch = () => {
    if (!selectedRepoId || !query.trim()) return;
    semanticSearch.mutate({ repositoryId: selectedRepoId, query: query.trim() });
  };

  const handleRepoClick = (repoId: string) => {
    navigate(`/repositories/${repoId}`);
    onClose();
  };

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4 bg-black/70 backdrop-blur-sm animate-fade-in"
    >
      <div className="bg-surface-1 border border-border rounded-xl shadow-overlay w-full max-w-xl animate-scale-in overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 border-b border-border">
          <Search className="h-4 w-4 text-text-quaternary flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && selectedRepoId) handleSemanticSearch();
            }}
            placeholder="Search repositories, actions, or code…"
            className="flex-1 py-3.5 text-sm bg-transparent text-text-primary placeholder-text-quaternary outline-none"
          />
          {query && (
            <button onClick={() => setQuery('')} className="text-text-quaternary hover:text-text-tertiary">
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="max-h-[50vh] overflow-y-auto">
          {/* Repositories */}
          {filteredRepos.length > 0 && (
            <div className="p-2">
              <div className="px-2 py-1.5 text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">
                Repositories
              </div>
              {filteredRepos.map((repo) => (
                <button
                  key={repo.id}
                  onClick={() => handleRepoClick(repo.id)}
                  className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-left hover:bg-surface-3 transition-colors group"
                >
                  <FolderGit2 className="h-4 w-4 text-text-quaternary group-hover:text-text-tertiary flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-text-primary truncate">{repo.repo_name}</div>
                    <div className="text-xs text-text-quaternary truncate">{repo.full_name}</div>
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-text-quaternary opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          )}

          {/* Semantic search section */}
          {query.trim() && repositories.length > 0 && (
            <div className="p-2 border-t border-border">
              <div className="px-2 py-1.5 text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">
                Semantic Code Search
              </div>
              <div className="px-3 py-2">
                <select
                  value={selectedRepoId || ''}
                  onChange={(e) => setSelectedRepoId(e.target.value || null)}
                  className="w-full text-sm bg-surface-3 border border-border rounded-lg px-3 py-2 text-text-primary outline-none focus:border-brand-500 mb-2"
                >
                  <option value="">Select a repository…</option>
                  {repositories
                    .filter((r) => r.indexing_status === 'completed' || r.indexing_status === 'complete')
                    .map((r) => (
                      <option key={r.id} value={r.id}>{r.full_name}</option>
                    ))}
                </select>
                <button
                  onClick={handleSemanticSearch}
                  disabled={!selectedRepoId || semanticSearch.isPending}
                  className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  {semanticSearch.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin-slow" />
                  ) : (
                    <FileCode2 className="h-4 w-4" />
                  )}
                  Search code for "{query.trim().slice(0, 30)}"
                </button>
              </div>

              {/* Semantic search results */}
              {semanticSearch.data && (
                <div className="px-3 pb-2 space-y-1.5">
                  {semanticSearch.data.results.length === 0 ? (
                    <p className="text-xs text-text-quaternary py-2">No matching code found.</p>
                  ) : (
                    semanticSearch.data.results.slice(0, 5).map((result, i) => (
                      <div key={i} className="p-2.5 bg-surface-3 border border-border rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <FileCode2 className="h-3 w-3 text-brand-400" />
                          <span className="text-xs font-medium text-brand-400 truncate">{result.file_path}</span>
                          <span className="ml-auto text-[10px] text-text-quaternary">
                            {(result.similarity * 100).toFixed(0)}% match
                          </span>
                        </div>
                        <pre className="text-xs text-text-tertiary overflow-x-auto line-clamp-3 whitespace-pre-wrap">
                          {result.chunk_text.slice(0, 200)}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {/* Quick actions */}
          {!query.trim() && (
            <div className="p-2 border-t border-border">
              <div className="px-2 py-1.5 text-[10px] font-semibold text-text-quaternary uppercase tracking-widest">
                Quick Actions
              </div>
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <button
                    key={action.label}
                    onClick={() => {
                      navigate(action.path);
                      onClose();
                    }}
                    className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-left hover:bg-surface-3 transition-colors group"
                  >
                    <Icon className="h-4 w-4 text-text-quaternary" />
                    <span className="text-sm text-text-secondary group-hover:text-text-primary">{action.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-border text-[10px] text-text-quaternary">
          <span>Type to search · ↵ to select · ESC to close</span>
        </div>
      </div>
    </div>
  );
}
