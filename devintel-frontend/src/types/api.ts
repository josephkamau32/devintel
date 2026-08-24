/**
 * DevIntel API types — mirrors backend Pydantic schemas.
 * These cover all endpoints the redesigned frontend consumes.
 */

/* ─── Analytics ─── */

export interface UsageTrend {
  date: string;
  queries: number;
}

export interface RepoUsage {
  repo_name: string;
  queries: number;
}

export interface AnalyticsDashboard {
  total_queries: number;
  total_tokens: number;
  total_repos_indexed: number;
  usage_trend: UsageTrend[];
  top_repositories: RepoUsage[];
  last_active_at: string | null;
}

/* ─── Health Score ─── */

export interface HealthDimensions {
  complexity: number;
  documentation: number;
  maintainability: number;
  test_coverage: number;
  security: number;
}

export interface HealthReport {
  id: string;
  repo_id: string;
  repo_name: string;
  overall_score: number;
  dimensions: HealthDimensions;
  summary: string;
  top_issues: string[];
  recommendations: string[];
  language_detected: string | null;
  files_analyzed: number;
  computed_at: string | null;
}

export interface HealthRefreshResponse {
  status: string;
  task_id: string;
  message: string;
}

export interface AutoFixResponse {
  status: string;
  pr_url: string | null;
  pr_number: number | null;
  branch_name: string | null;
  message: string | null;
}

/* ─── Architecture ─── */

export interface ArchitectureDiagram {
  id: string;
  repo_id: string;
  name: string;
  diagram_type: string;
  mermaid_code: string;
  created_at: string;
  updated_at: string;
}

export interface DiagramGenerateResponse {
  diagram: ArchitectureDiagram;
}

export interface DiagramListResponse {
  diagrams: ArchitectureDiagram[];
}

/* ─── PR Review ─── */

export interface PRReviewResponse {
  summary: string;
  potential_issues: string[];
  refactoring_suggestions: string[];
  security_warnings: string[];
  performance_notes: string[];
}

export interface PullRequest {
  number: number;
  title: string;
  state: string;
  author: string;
  author_avatar: string | null;
  created_at: string;
  updated_at: string;
  additions: number;
  deletions: number;
  url: string;
}

export interface PullRequestListResponse {
  pulls: PullRequest[];
  repository_id: string;
}

/* ─── Chat ─── */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  id: string;
  repository_id: string;
  question: string;
  response: string;
  token_usage: number;
  response_time_ms: number | null;
  agent_type: string | null;
  created_at: string;
}

export interface FileChange {
  path: string;
  content: string;
}

export interface DraftPayload {
  branch_name: string;
  pr_title: string;
  pr_body: string;
  commit_message: string;
  file_changes: FileChange[];
  generate_tests?: boolean;
}

export interface AgentDraftResponse {
  draft: DraftPayload;
}

export interface AgentExecuteResponse {
  pr_url: string;
  pr_number: number;
  branch_name: string;
}

/* ─── Git History ─── */

export interface GitHistoryEntry {
  sha: string;
  message: string;
  author_name: string;
  author_email: string;
  authored_date: string;
  committed_date: string;
  additions: number;
  deletions: number;
  files_changed: number;
}

/* ─── Indexing Status ─── */

export interface IndexingStatusResponse {
  id: string;
  indexing_status: string;
  indexing_progress: number;
  indexing_error: string | null;
  last_indexed_at: string | null;
  last_indexed_commit_sha: string | null;
  indexing_mode: string | null;
}

/* ─── Search ─── */

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

/* ─── Policy ─── */

export interface Policy {
  id: string;
  repository_id: string;
  name: string;
  description: string;
  rules: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyListResponse {
  policies: Policy[];
}
