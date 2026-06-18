export type IndexingStatus = "pending" | "cloning" | "chunking" | "embedding" | "completed" | "failed";

export interface Repository {
  id: number;
  user_id: number;
  github_repo_id: string | null;
  full_name: string;
  repo_name: string;
  description: string | null;
  url: string | null;
  stars: number;
  language: string | null;
  default_branch: string;
  is_private: boolean;
  indexing_status: IndexingStatus;
  last_indexed_commit: string | null;
}

export interface RepositoryListResponse {
  repositories: Repository[];
  total: number;
}

export interface SearchResult {
  file_path: string;
  chunk_text: string;
  similarity: number;
  chunk_index: number;
}

export interface SearchResponse {
  results: SearchResult[];
  repository_id: number;
  query: string;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  html_url: string;
  description: string | null;
  stargazers_count: number;
  language: string | null;
  default_branch: string;
}
