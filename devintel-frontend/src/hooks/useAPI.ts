import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/axios';
import type {
  AnalyticsDashboard,
  HealthReport,
  HealthRefreshResponse,
  AutoFixResponse,
  DiagramGenerateResponse,
  DiagramListResponse,
  PRReviewResponse,
  PullRequestListResponse,
  GitHistoryEntry,
  IndexingStatusResponse,
  SearchResponse,
} from '../types/api';
import type { Repository } from '../types/repository';

/* ─── Analytics ─── */

export function useAnalytics() {
  return useQuery<AnalyticsDashboard>({
    queryKey: ['analytics', 'dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/analytics/dashboard');
      return data;
    },
    staleTime: 1000 * 60 * 2,
    retry: 1,
  });
}

/* ─── Health Score ─── */

export function useHealthScore(repositoryId: string | undefined) {
  return useQuery<HealthReport>({
    queryKey: ['health', repositoryId],
    queryFn: async () => {
      const { data } = await api.get(`/repos/${repositoryId}/health`);
      return data;
    },
    enabled: !!repositoryId,
    staleTime: 1000 * 60 * 5,
    retry: false,
  });
}

export function useRefreshHealth() {
  const qc = useQueryClient();
  return useMutation<HealthRefreshResponse, Error, string>({
    mutationFn: async (repositoryId: string) => {
      const { data } = await api.post(`/repos/${repositoryId}/health/refresh`);
      return data;
    },
    onSuccess: (_data, repositoryId) => {
      // Invalidate health after a short delay to allow backend processing
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ['health', repositoryId] });
      }, 5000);
    },
  });
}

export function useAutoFix() {
  return useMutation<AutoFixResponse, Error, { repositoryId: string; issueDescription: string }>({
    mutationFn: async ({ repositoryId, issueDescription }) => {
      const { data } = await api.post(`/repos/${repositoryId}/auto-fix`, {
        issue_description: issueDescription,
      });
      return data;
    },
  });
}

/* ─── Aggregate health for all repos ─── */

export function useAllHealthScores(repositories: Repository[]) {
  return useQuery<Record<string, HealthReport>>({
    queryKey: ['health', 'all', repositories.map((r) => r.id).join(',')],
    queryFn: async () => {
      const results: Record<string, HealthReport> = {};
      const settled = await Promise.allSettled(
        repositories.map(async (repo) => {
          const { data } = await api.get(`/repos/${repo.id}/health`);
          return { id: repo.id, data };
        }),
      );
      for (const result of settled) {
        if (result.status === 'fulfilled') {
          results[result.value.id] = result.value.data;
        }
      }
      return results;
    },
    enabled: repositories.length > 0,
    staleTime: 1000 * 60 * 5,
    retry: false,
  });
}

/* ─── Architecture ─── */

export function useArchitectureDiagrams(repositoryId: string | undefined) {
  return useQuery<DiagramListResponse>({
    queryKey: ['architecture', 'diagrams', repositoryId],
    queryFn: async () => {
      const { data } = await api.get(`/architecture/diagrams/${repositoryId}`);
      return data;
    },
    enabled: !!repositoryId,
    staleTime: 1000 * 60 * 10,
    retry: false,
  });
}

export function useGenerateDiagram() {
  const qc = useQueryClient();
  return useMutation<DiagramGenerateResponse, Error, { repositoryId: string; diagramType: string; focusPaths?: string[] }>({
    mutationFn: async ({ repositoryId, diagramType, focusPaths }) => {
      const { data } = await api.post('/architecture/diagrams/generate', {
        repository_id: repositoryId,
        diagram_type: diagramType,
        focus_paths: focusPaths || null,
      });
      return data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['architecture', 'diagrams', variables.repositoryId] });
    },
  });
}

/* ─── PR Review ─── */

export function usePullRequests(repositoryId: string | undefined) {
  return useQuery<PullRequestListResponse>({
    queryKey: ['pulls', repositoryId],
    queryFn: async () => {
      const { data } = await api.get(`/repos/${repositoryId}/pulls`);
      return data;
    },
    enabled: !!repositoryId,
    staleTime: 1000 * 60 * 2,
    retry: 1,
  });
}

export function usePRReview() {
  return useMutation<PRReviewResponse, Error, { repositoryId: string; prNumber: number; prTitle: string; prDescription?: string }>({
    mutationFn: async ({ repositoryId, prNumber, prTitle, prDescription }) => {
      const { data } = await api.post('/pr-review', {
        repository_id: repositoryId,
        pr_number: prNumber,
        pr_title: prTitle,
        pr_description: prDescription || '',
      });
      return data;
    },
  });
}

export function usePRDiff(repositoryId: string | undefined, prNumber: number | undefined) {
  return useQuery<string>({
    queryKey: ['pulls', repositoryId, prNumber, 'diff'],
    queryFn: async () => {
      const { data } = await api.get(`/repos/${repositoryId}/pulls/${prNumber}/diff`);
      return data;
    },
    enabled: !!repositoryId && !!prNumber,
    staleTime: 1000 * 60 * 5,
  });
}

/* ─── Git History ─── */

export function useGitHistory(repositoryId: string | undefined) {
  return useQuery<GitHistoryEntry[]>({
    queryKey: ['gitHistory', repositoryId],
    queryFn: async () => {
      const { data } = await api.get(`/git/history/${repositoryId}`);
      return data;
    },
    enabled: !!repositoryId,
    staleTime: 1000 * 60 * 5,
    retry: 1,
  });
}

/* ─── Indexing Status ─── */

export function useIndexingStatus(repositoryId: string | undefined) {
  return useQuery<IndexingStatusResponse>({
    queryKey: ['indexingStatus', repositoryId],
    queryFn: async () => {
      const { data } = await api.get(`/repos/${repositoryId}/status`);
      return data;
    },
    enabled: !!repositoryId,
    staleTime: 1000 * 10,
    refetchInterval: 15000,
  });
}

/* ─── Repository Detail ─── */

export function useRepository(repositoryId: string | undefined) {
  return useQuery<Repository>({
    queryKey: ['repository', repositoryId],
    queryFn: async () => {
      const { data } = await api.get(`/repos/${repositoryId}`);
      return data;
    },
    enabled: !!repositoryId,
    staleTime: 1000 * 30,
  });
}

/* ─── Semantic Search ─── */

export function useSemanticSearch() {
  return useMutation<SearchResponse, Error, { repositoryId: string; query: string }>({
    mutationFn: async ({ repositoryId, query }) => {
      const { data } = await api.get(`/repos/${repositoryId}/search`, {
        params: { q: query },
      });
      return data;
    },
  });
}

/* ─── Delete Repository ─── */

export function useDeleteRepository() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (repositoryId: string) => {
      await api.delete(`/repos/${repositoryId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['repositories'] });
    },
  });
}
