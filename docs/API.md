# DevIntel API Documentation

## Base URL
- **Production**: `https://api.devintel.ai`
- **Development**: `http://localhost:8000`

## Authentication

All API endpoints (except `/auth/*`) require JWT authentication.

### Headers
```
Authorization: Bearer {access_token}
X-CSRF-Token: {csrf_token}
```

---

## Authentication Endpoints

### GitHub OAuth Login
```http
GET /api/v1/auth/github
```

**Response**:
```json
{
  "url": "https://github.com/login/oauth/authorize?client_id=..."
}
```

### OAuth Callback
```http
GET /api/v1/auth/github/callback?code={code}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "github_id": "string",
    "email": "user@example.com",
    "name": "User Name",
    "avatar_url": "https://...",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Refresh Access Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Get Current User
```http
GET /api/v1/auth/me
```

---

## Repository Endpoints

### List User Repositories
```http
GET /api/v1/repos
```

**Query Parameters**:
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 50, max: 100): Number of records to return

**Response**:
```json
[
  {
    "id": "uuid",
    "owner": "username",
    "name": "repo-name",
    "full_name": "username/repo-name",
    "description": "Repository description",
    "html_url": "https://github.com/username/repo-name",
    "default_branch": "main",
    "is_indexed": true,
    "indexing_status": "completed",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Add Repository
```http
POST /api/v1/repos
Content-Type: application/json

{
  "full_name": "owner/repo",
  "auto_index": true
}
```

**Response**: `202 Accepted`
```json
{
  "message": "Repository added successfully. Indexing started.",
  "repository_id": "uuid"
}
```

### Get Repository
```http
GET /api/v1/repos/{repo_id}
```

### Delete Repository
```http
DELETE /api/v1/repos/{repo_id}
```

**Response**: `204 No Content`

---

## Chat Endpoints

### Chat with RAG
```http
POST /api/v1/chat
Content-Type: application/json

{
  "question": "How does authentication work?",
  "repo_id": "uuid",
  "stream": true
}
```

**Response** (Server-Sent Events):
```
data: {"type": "thinking", "content": "Analyzing codebase..."}

data: {"type": "chunk", "content": "The authentication system uses"}

data: {"type": "chunk", "content": " JWT tokens with..."}

data: {"type": "done", "chat_id": "uuid"}
```

### Get Chat History
```http
GET /api/v1/chats?repo_id={repo_id}
```

---

## Analytics Endpoints

### Get User Analytics
```http
GET /api/v1/analytics/user
```

**Response**:
```json
{
  "total_repositories": 10,
  "total_files_indexed": 1500,
  "total_chats": 45,
  "recent_activity": [...],
  "top_repositories": [...]
}
```

---

## Health & Metrics

### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### Prometheus Metrics
```http
GET /metrics
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input: Suspicious pattern detected"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "CSRF token invalid"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "full_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limits

| Endpoint Pattern | Limit |
|--|--|
| `/api/v1/auth/*` | 5 requests/minute |
| `/api/v1/chat` | 20 requests/minute |
| `/api/v1/repos` (POST) | 3 requests/minute |
| Global | 100 requests/minute |

---

## Security

- All requests must use HTTPS in production
- CSRF protection required for state-changing operations
- SQL injection detection enabled
- Path traversal prevention active
- Request size limit: 10MB

---

## SDKs & Examples

### Python
```python
import requests

# Login and get token
response = requests.get("http://localhost:8000/api/v1/auth/github")
# Follow OAuth flow...

# Use API
headers = {
    "Authorization": f"Bearer {access_token}",
    "X-CSRF-Token": csrf_token,
}

repos = requests.get(
    "http://localhost:8000/api/v1/repos",
    headers=headers
).json()
```

### JavaScript
```javascript
import { apiClient } from './lib/api-client';

// API client handles auth automatically
const repos = await apiClient.get('/api/v1/repos');
const chat = await apiClient.post('/api/v1/chat', {
  question: 'How does this work?',
  repo_id: repoId,
});
```
