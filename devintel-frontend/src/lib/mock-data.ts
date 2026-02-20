// Mock data for the DevIntel AI platform
// NOTE: Repository-related mock data has been removed — the Repositories page
// now uses real backend API calls via useRepositories hook.

export interface ChatMessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface PullRequest {
  id: string;
  title: string;
  author: string;
  authorAvatar: string;
  status: 'open' | 'merged' | 'closed';
  createdAt: string;
  repository: string;
  additions: number;
  deletions: number;
  aiSummary?: string;
  suggestedChanges?: string[];
}

export interface ActivityItem {
  id: string;
  type: 'index' | 'chat' | 'pr_review' | 'alert';
  message: string;
  timestamp: string;
}

export const mockChatMessages: ChatMessageData[] = [
  { id: '1', role: 'user', content: 'How does the authentication middleware work in the api-gateway?', timestamp: '10:32 AM' },
  { id: '2', role: 'assistant', content: 'The authentication middleware in `api-gateway` follows a token-based approach. Here\'s how it works:\n\n```go\nfunc AuthMiddleware(next http.Handler) http.Handler {\n  return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n    token := r.Header.Get("Authorization")\n    if token == "" {\n      http.Error(w, "Unauthorized", 401)\n      return\n    }\n    claims, err := validateJWT(token)\n    if err != nil {\n      http.Error(w, "Invalid token", 403)\n      return\n    }\n    ctx := context.WithValue(r.Context(), "user", claims)\n    next.ServeHTTP(w, r.WithContext(ctx))\n  })\n}\n```\n\nThe middleware extracts the JWT from the `Authorization` header, validates it using the `validateJWT` function, and injects the user claims into the request context. If validation fails, it returns a 401 or 403 status.', timestamp: '10:32 AM' },
  { id: '3', role: 'user', content: 'What about rate limiting?', timestamp: '10:35 AM' },
  { id: '4', role: 'assistant', content: 'Rate limiting is implemented using a token bucket algorithm in `pkg/ratelimit/limiter.go`. Each authenticated user gets a bucket with:\n\n- **Capacity:** 100 requests\n- **Refill rate:** 10 requests/second\n\nThe middleware checks the bucket before processing:\n\n```go\nfunc RateLimitMiddleware(limiter *RateLimiter) Middleware {\n  return func(next http.Handler) http.Handler {\n    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {\n      userID := r.Context().Value("user").(Claims).ID\n      if !limiter.Allow(userID) {\n        w.Header().Set("Retry-After", "10")\n        http.Error(w, "Too Many Requests", 429)\n        return\n      }\n      next.ServeHTTP(w, r)\n    })\n  }\n}\n```\n\nExceeded limits return a `429` with a `Retry-After` header.', timestamp: '10:35 AM' },
];

export const mockPullRequests: PullRequest[] = [
  { id: '1', title: 'feat: Add WebSocket support for real-time notifications', author: 'sarah-chen', authorAvatar: '', status: 'open', createdAt: '2 hours ago', repository: 'frontend-app', additions: 342, deletions: 28, aiSummary: 'This PR adds WebSocket support for real-time notifications. The implementation follows a clean event-driven architecture with proper error handling and reconnection logic.', suggestedChanges: ['Consider adding a heartbeat mechanism to detect stale connections', 'The reconnection backoff should use exponential delay', 'Add unit tests for the WebSocket manager class'] },
  { id: '2', title: 'fix: Resolve memory leak in connection pooling', author: 'alex-dev', authorAvatar: '', status: 'open', createdAt: '5 hours ago', repository: 'api-gateway', additions: 45, deletions: 12, aiSummary: 'Fixes a memory leak caused by connections not being properly released back to the pool when requests timeout.', suggestedChanges: ['Add a connection health check before reuse', 'Consider implementing a max connection age policy'] },
  { id: '3', title: 'refactor: Migrate data layer to repository pattern', author: 'mike-r', authorAvatar: '', status: 'merged', createdAt: '1 day ago', repository: 'api-gateway', additions: 567, deletions: 389 },
  { id: '4', title: 'chore: Update dependencies and fix security vulnerabilities', author: 'bot-renovate', authorAvatar: '', status: 'merged', createdAt: '2 days ago', repository: 'frontend-app', additions: 120, deletions: 98 },
];

export const mockActivities: ActivityItem[] = [
  { id: '1', type: 'index', message: 'Repository frontend-app re-indexed successfully', timestamp: '2 min ago' },
  { id: '2', type: 'chat', message: 'AI Chat session completed — 4 queries answered', timestamp: '15 min ago' },
  { id: '3', type: 'pr_review', message: 'PR #142 reviewed with 3 suggestions', timestamp: '1 hour ago' },
  { id: '4', type: 'alert', message: 'New security advisory detected in ml-pipeline', timestamp: '2 hours ago' },
  { id: '5', type: 'index', message: 'Repository api-gateway indexed — 156 files processed', timestamp: '5 hours ago' },
];

export const mockAnalyticsData = {
  aiUsage: [
    { date: 'Mon', queries: 24 },
    { date: 'Tue', queries: 18 },
    { date: 'Wed', queries: 32 },
    { date: 'Thu', queries: 45 },
    { date: 'Fri', queries: 38 },
    { date: 'Sat', queries: 12 },
    { date: 'Sun', queries: 8 },
  ],
  topFiles: [
    { file: 'src/auth/middleware.go', queries: 45 },
    { file: 'src/api/handlers.go', queries: 38 },
    { file: 'src/components/App.tsx', queries: 32 },
    { file: 'pkg/ratelimit/limiter.go', queries: 28 },
    { file: 'src/utils/helpers.ts', queries: 22 },
  ],
  complexity: [
    { date: 'Week 1', score: 72 },
    { date: 'Week 2', score: 68 },
    { date: 'Week 3', score: 74 },
    { date: 'Week 4', score: 65 },
  ],
};

// Mock API service functions
export const api = {
  getChatMessages: () => Promise.resolve(mockChatMessages),
  getPullRequests: () => Promise.resolve(mockPullRequests),
  getActivities: () => Promise.resolve(mockActivities),
  getAnalytics: () => Promise.resolve(mockAnalyticsData),
  sendChatMessage: (message: string) => {
    return new Promise<ChatMessageData>((resolve) => {
      setTimeout(() => {
        resolve({
          id: Date.now().toString(),
          role: 'assistant',
          content: `I've analyzed your question about "${message.slice(0, 50)}..."\n\nBased on the codebase, here's what I found:\n\n\`\`\`typescript\n// Relevant code snippet\nconst result = processQuery(input);\nconsole.log(result);\n\`\`\`\n\nThis pattern is used across the codebase for consistent data processing.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
      }, 1500);
    });
  },
};
