# DevIntel AI - Security Enhancements

## Security Features Implemented

This document outlines the comprehensive security measures implemented in the DevIntel backend.

### 1. Security Middleware

#### Security Headers Middleware
Implements OWASP security best practices via HTTP headers:

- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
- **X-Frame-Options**: `DENY` - Prevents clickjacking attacks
- **X-XSS-Protection**: `1; mode=block` - Legacy XSS protection
- **Strict-Transport-Security**: Forces HTTPS connections (production)
- **Content-Security-Policy**: Restricts resource loading
- **Referrer-Policy**: Controls referrer information
- **Permissions-Policy**: Restricts browser features

#### Request ID Middleware
- Generates unique ID for each request
- Enables distributed tracing
- Adds ID to response headers and logs
- Facilitates debugging and monitoring

#### Request Size Limit Middleware
- Limits request body to 10MB by default
- Prevents DoS attacks via large payloads
- Returns 413 status for oversized requests

#### Audit Logging Middleware
Logs sensitive operations including:
- All authentication attempts
- Repository modifications
- User data access
- Admin operations

Logged information:
- Request method and path
- Client IP and User-Agent
- Request ID for tracing
- Response status and duration

#### SQL Injection Detection Middleware
- Logs suspicious SQL patterns in queries
- Defense-in-depth measure (primary: parameterized queries)
- Alerts security team of potential attacks

### 2. Input Validation

Comprehensive validators prevent injection attacks:

#### GitHub URL Validation
- Ensures HTTPS protocol
- Verifies github.com domain
- Validates repository path format
- Prevents SSRF attacks

#### Repository Name Validation
- Enforces `user/repo` format
- Allows only safe characters
- Prevents path traversal
- Maximum 100 characters

#### User Input Sanitization
- Removes null bytes
- Length validation (max 10,000 chars)
- Trims whitespace
- Prevents XSS attacks

#### Pagination Validation
- Prevents integer overflow
- Limits page size (max 100)
- Reasonable page number limits
- Prevents DoS via large requests

#### Email Validation
- RFC-compliant format checking
- Maximum length validation (320 chars)
- Lowercase normalization

#### UUID Validation
- Validates UUID v4 format
- Prevents malformed IDs
- Consistent error messages

#### Chat Question Validation
- Minimum 3 characters
- Maximum 5,000 characters
- Sanitized for XSS
- Empty string prevention

### 3. Authentication Security

#### JWT Tokens
- Secure token generation with HS256
- Configurable expiration (default 24 hours)
- Token validation middleware
- Protected endpoints require valid tokens

#### GitHub OAuth
- Secure OAuth 2.0 flow
- State parameter for CSRF protection
- Token exchange over HTTPS
- User data validation

### 4. Rate Limiting

- IP-based rate limiting: 100 requests/minute
- Prevents brute force attacks
- Prevents DoS attacks
- Configurable limits per endpoint

### 5. CORS Configuration

Strict CORS policy:
- Explicit origin whitelist
- No wildcard (`*`) in production
- Credentials allowed only for trusted origins
- Preflight request handling

### 6. Database Security

- **Parameterized Queries**: SQLAlchemy ORM prevents SQL injection
- **Connection Pooling**: Limited connections prevent exhaustion
- **Async Queries**: Non-blocking database operations
- **Input Validation**: All user input validated before queries

### 7. Secret Management

- Environment variables for all secrets
- Never hardcoded in source code
- Production-specific values
- Rotation recommendations in documentation

### 8. Error Handling

- Generic error messages to users
- Detailed logging for debugging
- No sensitive information in responses
- Stack traces only in development

### 9. Logging

- Structured JSON logging in production
- Request/response logging
- Security event logging
- No PII in logs (passwords, tokens redacted)

### 10. Production Recommendations

See `.env.example` for production checklistincluding:

1. Set `ENVIRONMENT=production`
2. Set `DEBUG=false`
3. Generate strong `SECRET_KEY` and `JWT_SECRET_KEY`
4. Use managed database and Redis
5. Configure strict CORS origins
6. Enable HTTPS
7. Set up monitoring (Sentry)
8. Configure log aggregation
9. Regular security audits
10. Dependency vulnerability scanning

## Security Testing

Run security tests:

```bash
# Run all security-related tests
pytest tests/test_api/ -k security -v

# Test authentication
pytest tests/test_api/test_auth.py -v

# Test input validation
pytest tests/test_core/test_validators.py -v
```

## Reporting Security Issues

If you discover a security vulnerability, please email: security@devintel.ai

Do NOT open a public issue for security vulnerabilities.

## Security Compliance

DevIntel follows:
- OWASP Top 10 protection
- SANS Top 25 mitigation
- CWE (Common Weakness Enumeration) prevention
- Zero Trust architecture principles

Last security audit: 2026-02-12
Next audit: TBD
