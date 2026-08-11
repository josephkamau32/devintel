import { useOutletContext, useNavigate } from 'react-router-dom';
import { useIndexingStatus, useDeleteRepository } from '../../hooks/useAPI';
import { indexRepository } from '../../hooks/useRepositories';
import type { Repository } from '../../types/repository';
import { RotateCw, Trash2, Loader2, CheckCircle2, AlertTriangle, Database } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';

export function SettingsTab() {
  const { repository } = useOutletContext<{ repository: Repository }>();
  const { data: status } = useIndexingStatus(repository.id);
  const deleteRepo = useDeleteRepository();
  const navigate = useNavigate();
  const [isIndexing, setIsIndexing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleReindex = async () => {
    setIsIndexing(true);
    try {
      await indexRepository(repository.id);
      toast.success('Re-indexing started.');
    } catch {
      toast.error('Failed to start re-indexing.');
    } finally {
      setIsIndexing(false);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteRepo.mutateAsync(repository.id);
      toast.success('Repository disconnected.');
      navigate('/repositories');
    } catch {
      toast.error('Failed to delete repository.');
    }
  };

  return (
    <div className="space-y-6 max-w-2xl animate-fade-in">
      <h2 className="text-h3 text-text-primary">Repository Settings</h2>

      {/* Repository info */}
      <div className="card">
        <div className="px-5 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Repository Information</h3>
        </div>
        <div className="p-5 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-text-tertiary">Name</span>
            <span className="text-text-primary font-medium">{repository.full_name}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-text-tertiary">Language</span>
            <span className="text-text-primary">{repository.language || 'Unknown'}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-text-tertiary">Default Branch</span>
            <span className="text-text-primary font-mono text-xs bg-surface-4 px-2 py-0.5 rounded">{repository.default_branch}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-text-tertiary">Visibility</span>
            <span className="text-text-primary">{repository.is_private ? 'Private' : 'Public'}</span>
          </div>
        </div>
      </div>

      {/* Indexing status */}
      <div className="card">
        <div className="px-5 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Indexing</h3>
        </div>
        <div className="p-5 space-y-4">
          <div className="flex items-center gap-3">
            {repository.indexing_status === 'completed' || repository.indexing_status === 'complete' ? (
              <CheckCircle2 className="h-5 w-5 text-status-success" />
            ) : ['pending', 'indexing', 'cloning', 'chunking', 'embedding'].includes(repository.indexing_status) ? (
              <Loader2 className="h-5 w-5 text-status-info animate-spin-slow" />
            ) : (
              <Database className="h-5 w-5 text-text-quaternary" />
            )}
            <div>
              <p className="text-sm font-medium text-text-primary capitalize">{repository.indexing_status || 'Not indexed'}</p>
              {status?.last_indexed_at && (
                <p className="text-xs text-text-quaternary">Last indexed: {new Date(status.last_indexed_at).toLocaleString()}</p>
              )}
            </div>
          </div>

          {status?.indexing_progress !== undefined && status.indexing_progress > 0 && status.indexing_progress < 100 && (
            <div className="score-bar-track">
              <div className="score-bar-fill bg-brand-500" style={{ width: `${status.indexing_progress}%` }} />
            </div>
          )}

          {status?.indexing_error && (
            <div className="flex items-center gap-2 p-3 bg-status-error-muted border border-status-error/20 rounded-lg text-sm text-status-error">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              {status.indexing_error}
            </div>
          )}

          <button
            onClick={handleReindex}
            disabled={isIndexing}
            className="flex items-center gap-2 bg-surface-3 hover:bg-surface-4 border border-border text-text-primary px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isIndexing ? <Loader2 className="h-4 w-4 animate-spin-slow" /> : <RotateCw className="h-4 w-4" />}
            Re-index Repository
          </button>
        </div>
      </div>

      {/* Danger zone */}
      <div className="card border-status-error/20">
        <div className="px-5 py-3 border-b border-status-error/20">
          <h3 className="text-sm font-semibold text-status-error">Danger Zone</h3>
        </div>
        <div className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-text-primary">Disconnect Repository</p>
              <p className="text-xs text-text-quaternary mt-0.5">Remove this repository and all its data from DevIntel.</p>
            </div>
            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 bg-status-error-muted hover:bg-status-error/20 border border-status-error/20 text-status-error px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              >
                <Trash2 className="h-3 w-3" />
                Disconnect
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-3 py-1.5 text-xs font-medium text-text-tertiary hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleteRepo.isPending}
                  className="flex items-center gap-2 bg-status-error hover:bg-red-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {deleteRepo.isPending ? <Loader2 className="h-3 w-3 animate-spin-slow" /> : <Trash2 className="h-3 w-3" />}
                  Confirm
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
