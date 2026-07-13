import useSWR from 'swr';
import { api } from '../lib/axios';
import { RepositoryListResponse, GitHubRepository } from '../types/repository';

export function useRepositories(page: number = 1, limit: number = 50) {
  const { data, error, mutate, isLoading } = useSWR<RepositoryListResponse>(
    `/repos?skip=${(page - 1) * limit}&limit=${limit}`,
    async (url: string) => {
      const res = await api.get(url);
      return res.data;
    }
  );

  return {
    repositories: data?.repositories || [],
    total: data?.total || 0,
    isLoading,
    isError: error,
    mutate
  };
}

export function useGitHubRepositories(page: number = 1, perPage: number = 30) {
  const { data, error, mutate, isLoading } = useSWR<{ repositories: GitHubRepository[], page: number, per_page: number }>(
    `/repos/github?page=${page}&per_page=${perPage}`,
    async (url: string) => {
      const res = await api.get(url);
      return res.data;
    }
  );

  return {
    githubRepositories: data?.repositories || [],
    isLoading,
    isError: error,
    mutate
  };
}

export async function connectRepository(repo: GitHubRepository) {
  const response = await api.post('/repos', {
    repo_name: repo.name,
    full_name: repo.full_name,
    url: repo.html_url,
    description: repo.description,
    stars: repo.stargazers_count,
    language: repo.language,
    default_branch: repo.default_branch
  });
  return response.data;
}

export async function indexRepository(repositoryId: number) {
  const response = await api.post('/repos/index', {
    repository_id: repositoryId
  });
  return response.data;
}

