import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/axios';
import { RepositoryListResponse, GitHubRepository } from '../types/repository';

/**
 * Fetch connected repositories — migrated from SWR to TanStack Query
 * for consistency with the rest of the app's data fetching.
 */
export function useRepositories(page: number = 1, limit: number = 50) {
  const queryResult = useQuery<RepositoryListResponse>({
    queryKey: ['repositories', page, limit],
    queryFn: async () => {
      const res = await api.get(`/repos?skip=${(page - 1) * limit}&limit=${limit}`);
      return res.data;
    },
    staleTime: 1000 * 30, // 30s — repos change infrequently
    refetchOnWindowFocus: true,
  });

  return {
    repositories: queryResult.data?.repositories || [],
    total: queryResult.data?.total || 0,
    isLoading: queryResult.isLoading,
    isError: queryResult.isError,
    mutate: queryResult.refetch,
  };
}

/**
 * Fetch GitHub repositories available for connection.
 */
export function useGitHubRepositories(page: number = 1, perPage: number = 30) {
  const queryResult = useQuery<{ repositories: GitHubRepository[]; page: number; per_page: number }>({
    queryKey: ['githubRepositories', page, perPage],
    queryFn: async () => {
      const res = await api.get(`/repos/github?page=${page}&per_page=${perPage}`);
      return res.data;
    },
    staleTime: 1000 * 60 * 2, // 2 min cache
  });

  return {
    githubRepositories: queryResult.data?.repositories || [],
    isLoading: queryResult.isLoading,
    isError: queryResult.isError,
    mutate: queryResult.refetch,
  };
}

/**
 * Connect a GitHub repository to DevIntel.
 */
export function useConnectRepository() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (repo: GitHubRepository) => {
      const response = await api.post('/repos', {
        repo_name: repo.repo_name,
        full_name: repo.full_name,
        url: repo.url,
        description: repo.description,
        stars: repo.stars,
        language: repo.language,
        default_branch: repo.default_branch,
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate repos list so it refetches
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
    },
  });
}

/**
 * Connect repository — standalone function for components that need it.
 */
export async function connectRepository(repo: GitHubRepository) {
  const response = await api.post('/repos', {
    repo_name: repo.repo_name,
    full_name: repo.full_name,
    url: repo.url,
    description: repo.description,
    stars: repo.stars,
    language: repo.language,
    default_branch: repo.default_branch,
  });
  return response.data;
}

/**
 * Trigger indexing on a connected repository.
 */
export async function indexRepository(repositoryId: string) {
  const response = await api.post('/repos/index', {
    repository_id: repositoryId,
  });
  return response.data;
}
