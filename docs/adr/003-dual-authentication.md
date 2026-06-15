# ADR-003: Dual Authentication Strategy (GitHub OAuth + Email/Password)

## Status
Accepted

## Context
Users have different preferences for authentication:
1. GitHub OAuth - seamless for developers
2. Email/password - traditional and universal

Both approaches need to integrate with the same JWT-based session management.

## Decision
Implement both authentication methods:
- GitHub OAuth for developer-first experience
- Email/password as fallback

Use JWT with short-lived access tokens (15 min) and longer refresh tokens (7 days). Store refresh tokens as SHA-256 hashes to prevent database compromise attacks.

## Consequences
- **Positive**: Flexible authentication options
- **Positive**: Enhanced security with token hashing
- **Positive**: Token rotation on refresh
- **Negative**: Dual maintenance burden

## Implementation
- `/api/v1/auth/signup` - email/password registration
- `/api/v1/auth/login` - email/password authentication
- `/api/v1/auth/github` - OAuth redirect
- `/api/v1/auth/github/callback` - OAuth callback handler
- `/api/v1/auth/refresh` - token refresh with rotation
- `/api/v1/auth/logout` - server-side token invalidation

## Security Considerations
- Rate limiting on auth endpoints (5/minute)
- CSRF protection via double-submit cookie pattern
- Refresh token stored as hash, never plaintext
- JWT secret rotated separately from refresh tokens