export type IndexingStatus = "pending" | "indexing" | "complete" | "completed" | "cloning" | "chunking" | "embedding" | "failed";

export interface Repository {
  id: string;
  user_id: string;
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
  repository_id: string;
  query: string;
}

export interface GitHubRepository {
  repo_name: string;
  full_name: string;
  description: string | null;
  url: string;
  clone_url: string;
  stars: number;
  language: string | null;
  private: boolean;
  default_branch: string;
}

