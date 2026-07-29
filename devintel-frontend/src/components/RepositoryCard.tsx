import React from 'react';
import { Github, Play, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Repository } from '../types/repository';

interface RepositoryCardProps {
  repository: Repository;
  onIndex: (id: string) => void;
}

export const RepositoryCard: React.FC<RepositoryCardProps> = ({ repository, onIndex }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="text-green-500 w-5 h-5" />;
      case 'failed': return <XCircle className="text-red-500 w-5 h-5" />;
      case 'pending': 
      case 'cloning': 
      case 'chunking': 
      case 'embedding': 
        return <Loader2 className="text-blue-500 w-5 h-5 animate-spin" />;
      default: return null;
    }
  };

  const isIndexing = ['pending', 'cloning', 'chunking', 'embedding'].includes(repository.indexing_status);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-blue-500/50 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-gray-800 p-2 rounded-lg">
            <Github className="w-6 h-6 text-gray-300" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">{repository.repo_name}</h3>
            <p className="text-sm text-gray-400">{repository.full_name}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon(repository.indexing_status)}
          <span className="text-sm font-medium text-gray-300 capitalize">
            {repository.indexing_status}
          </span>
        </div>
      </div>
      
      {repository.description && (
        <p className="text-gray-400 text-sm mb-4 line-clamp-2">{repository.description}</p>
      )}

      <div className="flex items-center justify-between mt-auto">
        <div className="flex space-x-4 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
            <span>{repository.language || 'Unknown'}</span>
          </div>
          <div className="flex items-center space-x-1">
            <span>⭐</span>
            <span>{repository.stars}</span>
          </div>
        </div>
        
        <button
          onClick={() => onIndex(repository.id)}
          disabled={isIndexing}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            isIndexing 
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {isIndexing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Indexing...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>{repository.indexing_status === 'completed' ? 'Re-Index' : 'Index'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
