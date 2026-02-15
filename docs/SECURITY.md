# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in DevIntel, please report it to **security@devintel.ai** or create a private security advisory on GitHub.

**DO NOT** create public issues for security vulnerabilities.

---

## Security Features

### 1. Authentication & Authorization

#### JWT Tokens
- **Access tokens**: 15-minute expiry
- **Refresh tokens**: 7-day expiry
- Tokens stored securely (HttpOnly cookies in production)
- HS256 algorithm with strong secret keys

#### GitHub OAuth
- Encrypted token storage using Fernet symmetric encryption
- Tokens stored as `github_access_token_encrypted` in database
- Never logged or exposed in responses

### 2. Input Validation

#### SQL Injection Prevention
- **Primary**: Parameterized queries via SQLAlchemy ORM
- **Defense in depth**: Middleware blocks suspicious patterns
- Real-time detection and blocking of:
  - SQL keywords (UNION, SELECT, DROP, etc.)
  - SQL comments (`--`, `/*`, `*/`)
  - Common injection patterns

#### Path Traversal Prevention
-Sanitization of all file paths
- Blocked patterns: `..`, `~`, `/../`, `\..\`
- Path resolution with allowed directory whitelisting

#### Repository Name Validation
- Regex pattern: `owner/repo-name`
- Alphanumeric, hyphens,underscores, and dots only

### 3. CSRF Protection

- Token-based protection for all POST/PUT/PATCH/DELETE requests
- Tokens validated via `X-CSRF-Token` header
- Secure, SameSite=strict cookies
- OAuth callbacks exempt from CSRF

### 4. Security Headers

All responses include:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

### 5. Rate Limiting

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `/api/v1/auth/*` | 5/min | Prevent brute force |
| `/api/v1/chat` | 20/min | Prevent abuse |
| `/api/v1/repos` (POST) | 3/min | Limit resource creation |
| Global | 100/min | Overall protection |

### 6. Request Security

- **Size limits**: 10MB maximum request size
- **Audit logging**: All sensitive operations logged
- **Request IDs**: Unique IDs for request tracing

---

## Data Protection

### Encryption at Rest
- **GitHub tokens**: Fernet symmetric encryption (AES-128-CBC)
- **Database**: PostgreSQL with encrypted volumes (production)
- **Redis**: In-memory, ephemeral data only

### Encryption in Transit
- **HTTPS**: Required in production (TLS 1.2+)
- **Database**: SSL/TLS connections enforced
- **Redis**: AUTH password protection

### Sensitive Data Handling
- Passwords: Never stored (GitHub OAuth only)
- API keys: Environment variables only
- Secrets: Never logged or returned in responses
- PII: Email addresses stored, not shared

---

## Security Best Practices

### For Developers

1. **Never commit secrets**
   - Use `.env` files (gitignored)
   - Use environment variables
   - Rotate secrets regularly

2. **Dependencies**
   - Run `pip audit` regularly
   - Keep dependencies updated
   - Review CVEs in dependency tree

3. **Code reviews**
   - Security-focused reviews for auth code
   - Validate input handling
   - Check for information disclosure

4. **Testing**
   - Run security tests in CI/CD
   - Test authentication flows
   - Validate input sanitization

### For Deployment

1. **Environment separation**
   - Separate dev, staging, production
   - Different secrets per environment
   - Principle of least privilege

2. **Monitoring**
   - Enable Sentry error tracking
   - Monitor Prometheus metrics
   - Review audit logs regularly

3. **Database**
   - Use strong passwords (16+ chars)
   - Enable SSL connections
   - Regular backups with encryption
   - Limit connection pool size

4. **Network**
   - Firewall rules (whitelist only)
   - Private networks for backend services
   - No direct database exposure

---

## Vulnerability Disclosure

### Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

### Known Issues

None currently.

### Security Updates

Security patches released as soon as possible after verification.

---

## Compliance

### GDPR
- User data deletion on request
- Email addresses are only PII stored
- No data sold to third parties
- Data retention: 90 days after account deletion

### OWASP Top 10

| Risk | Mitigation |
|------|------------|
| Injection | SQLAlchemy ORM + middleware detection |
| Broken Authentication | JWT with short expiry, refresh tokens |
| Sensitive Data Exposure | Encryption at rest/transit, no secrets in logs |
| XML External Entities | Not applicable (JSON only) |
| Broken Access Control | Authorization checks on all endpoints |
| Security Misconfiguration | Security headers, production hardening |
| XSS | Input sanitization, CSP headers |
| Insecure Deserialization | JSON only, validated schemas |
| Using Components with Known Vulnerabilities | Automated dependency scanning |
| Insufficient Logging & Monitoring | Audit logs, Sentry, Prometheus |

---

## Security Checklist for Production

- [ ] All secrets rotated from development
- [ ] HTTPS enforced (HTTP redirected)
- [ ] Database passwords 16+ characters
- [ ] TOKEN_ENCRYPTION_KEY set and secure
- [ ] JWT_SECRET_KEY different from development
- [ ] CORS origins restricted to production domains
- [ ] Sentry DSN configured
- [ ] Prometheus monitoring enabled
- [ ] Database backups automated
- [ ] Firewall rules configured
- [ ] SSL certificates valid
- [ ] Rate limiting verified
- [ ] Audit logging enabled

---

##Contact

Security questions: **security@devintel.ai**
