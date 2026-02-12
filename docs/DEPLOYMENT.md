# DevIntel Deployment Guide

## Table of Contents

- [Quick Deploy Options](#quick-deploy-options)
- [Production Architecture](#production-architecture)
- [Option 1: Railway (Recommended for Beginners)](#option-1-railway)
- [Option 2: Render](#option-2-render)
- [Option 3: DigitalOcean App Platform](#option-3-digitalocean)
- [Option 4: AWS ECS (Advanced)](#option-4-aws-ecs)
- [Option 5: Self-Hosted VPS](#option-5-self-hosted-vps)
- [Environment Variables](#environment-variables)
- [Post-Deployment Checklist](#post-deployment-checklist)

---

## Quick Deploy Options

| Platform | Difficulty | Cost | Best For |
|----------|-----------|------|----------|
| **Railway** | ⭐ Easy | ~$20/mo | Fast deployment, beginners |
| **Render** | ⭐ Easy | ~$25/mo | Simple setup, good DX |
| **DigitalOcean** | ⭐⭐ Medium | ~$30/mo | More control, predictable pricing |
| **AWS ECS** | ⭐⭐⭐ Hard | ~$40/mo | Enterprise, scalability |
| **Self-hosted VPS** | ⭐⭐⭐ Hard | ~$12/mo | Full control, cost-effective |

---

## Production Architecture

```
┌─────────────┐
│   Cloudflare│  ← CDN & DDoS Protection
│     DNS     │
└──────┬──────┘
       │
┌──────▼──────────────────────────────┐
│         Frontend (Vercel)            │
│  React + Vite + Static Assets        │
└──────┬──────────────────────────────┘
       │
┌──────▼──────────────────────────────┐
│      Backend API (Railway/Render)    │
│      FastAPI + Celery Workers        │
└──┬───────────────────────────────┬──┘
   │                               │
┌──▼────────────┐        ┌────────▼──────┐
│  PostgreSQL   │        │     Redis     │
│  (Neon/RDS)   │        │  (Upstash)    │
└───────────────┘        └───────────────┘
```

---

## Option 1: Railway (Recommended)

**Pros:** Extremely easy, auto-deploys from GitHub, built-in database
**Cons:** Can be expensive at scale

### Step-by-Step

#### 1. Deploy Backend

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd devintel-backend
railway init

# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis

# Deploy
railway up
```

#### 2. Configure Environment

In Railway dashboard, add environment variables:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Railway will auto-inject DATABASE_URL and REDIS_URL

GITHUB_CLIENT_ID=<your-github-oauth-app-id>
GITHUB_CLIENT_SECRET=<your-github-oauth-secret>
GITHUB_REDIRECT_URI=https://your-domain.com/auth/callback

OPENAI_API_KEY=<your-openai-api-key>

CORS_ORIGINS=https://your-frontend-domain.com
```

#### 3. Deploy Frontend to Vercel

```bash
cd devintel-frontend
npx vercel --prod

# Follow prompts:
# - Build command: npm run build
# - Output directory: dist
# - Environment variables: Add API URL
```

Add environment variable in Vercel:
```env
VITE_API_URL=https://your-backend.railway.app
```

#### 4. Set Up Custom Domain

In Railway:
- Go to Settings → Domains
- Add custom domain: `api.yourdomain.com`

In Vercel:
- Go to Settings → Domains
- Add custom domain: `yourdomain.com`

---

## Option 2: Render

**Pros:** Simple, free tier available
**Cons:** Cold starts on free tier

### Step-by-Step

#### 1. Create `render.yaml`

```yaml
services:
  # API Service
  - type: web
    name: devintel-api
    env: docker
    dockerfilePath: ./devintel-backend/docker/Dockerfile.api
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: devintel-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: devintel-redis
          type: redis
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET_KEY
        generateValue: true

  # Celery Worker
  - type: worker
    name: devintel-worker
    env: docker
    dockerfilePath: ./devintel-backend/docker/Dockerfile.worker
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: devintel-db
          property: connectionString

databases:
  - name: devintel-db
    databaseName: devintel
    plan: starter

  - name: devintel-redis
    plan: starter
```

#### 2. Deploy

1. Push code to GitHub
2. Go to Render dashboard
3. Click "New +" → "Blueprint"
4. Connect GitHub repo
5. Render auto-deploys from `render.yaml`

---

## Option 3: DigitalOcean App Platform

**Pros:** Predictable pricing, good docs
**Cons:** Slightly more expensive

### Step-by-Step

#### 1. Create App Spec

```yaml
name: devintel
services:
  - name: api
    source:
      repo_clone_url: https://github.com/yourusername/devintel
      branch: main
      deploy_on_push: true
    dockerfile_path: devintel-backend/docker/Dockerfile.api
    envs:
      - key: ENVIRONMENT
        value: production
    instance_count: 1
    instance_size_slug: basic-xxs

  - name: worker
    source:
      repo_clone_url: https://github.com/yourusername/devintel
      branch: main
    dockerfile_path: devintel-backend/docker/Dockerfile.worker
    instance_count: 1
    instance_size_slug: basic-xxs

databases:
  - engine: PG
    name: devintel-db
    production: true
    version: "16"

  - engine: REDIS
    name: devintel-redis
    production: true
```

#### 2. Deploy via CLI

```bash
# Install doctl
brew install doctl  # Mac
# or download from DigitalOcean

# Authenticate
doctl auth init

# Create app
doctl apps create --spec .do/app.yaml

# View deployment
doctl apps list
```

---

## Option 4: AWS ECS (Advanced)

For enterprise-grade deployment. See separate guide: `docs/AWS_DEPLOYMENT.md`

---

## Option 5: Self-Hosted VPS

**Pros:** Full control, cheapest
**Cons:** You manage everything

### Requirements

- Ubuntu 22.04 VPS ($12/mo on Linode, Hetzner, or DigitalOcean)
- Domain name
- 2GB RAM minimum

### Step-by-Step

#### 1. Initial Server Setup

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create application user
adduser devintel
usermod -aG docker devintel
su - devintel
```

#### 2. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/devintel.git
cd devintel/devintel-backend

# Create production .env
cp .env.example .env
nano .env  # Edit with production values
```

#### 3. Set Up Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/devintel
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/devintel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Set Up SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

#### 5. Start Application

```bash
cd ~/devintel/devintel-backend
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f
```

#### 6. Set Up Auto-Restart

```bash
# Create systemd service
sudo nano /etc/systemd/system/devintel.service
```

```ini
[Unit]
Description=DevIntel AI Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/devintel/devintel/devintel-backend
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=devintel

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable devintel
sudo systemctl start devintel
```

---

## Environment Variables

### Required for Production

```env
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<32-char-random-string>
JWT_SECRET_KEY=<32-char-random-string>

# Database (from provider)
DATABASE_URL=postgresql+asyncpg://...

# Redis (from provider)
REDIS_URL=redis://...

# GitHub OAuth
GITHUB_CLIENT_ID=<your-id>
GITHUB_CLIENT_SECRET=<your-secret>
GITHUB_REDIRECT_URI=https://yourdomain.com/auth/callback

# OpenAI
OPENAI_API_KEY=sk-...

# CORS
CORS_ORIGINS=https://yourdomain.com

# Security
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com
HTTPS_REDIRECT=true

# Monitoring (Optional)
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
```

### Generate Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

---

## Post-Deployment Checklist

### Security

- [ ] HTTPS enabled (SSL certificate)
- [ ] Environment variables set correctly
- [ ] `DEBUG=false` in production
- [ ] Strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Database credentials secured
- [ ] CORS configured for your domain only
- [ ] Firewall configured (only ports 80, 443, 22 open)

### Monitoring

- [ ] Sentry error tracking configured
- [ ] Logging configured
- [ ] Health check endpoint working: `/health`
- [ ] Uptime monitoring (UptimeRobot, Pingdom)

### Performance

- [ ] Database indexed properly
- [ ] Redis caching enabled
- [ ] CDN configured for frontend
- [ ] Compression enabled (Nginx gzip)

### Backup

- [ ] Database automated backups enabled
- [ ] Backup restore tested
- [ ] Environment variables backed up securely

### DNS

- [ ] A record pointing to server IP
- [ ] CNAME for www subdomain
- [ ] SPF/DKIM records (if sending emails)

---

## Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
docker-compose exec api python -c "from app.db.session import engine; print(engine.url)"
```

**CORS errors:**
- Ensure `CORS_ORIGINS` includes your frontend URL (with protocol)
- Check browser console for exact origin being blocked

**OAuth callback fails:**
- Verify `GITHUB_REDIRECT_URI` matches exactly in GitHub app settings
- Check that callback URL uses HTTPS in production

**502 Bad Gateway:**
- API is not running: `docker-compose ps`
- Check logs: `docker-compose logs api`
- Nginx config error: `nginx -t`

---

## Scaling

### Horizontal Scaling

Add more API instances behind a load balancer:

```yaml
services:
  api:
    deploy:
      replicas: 3  # Run 3 instances
```

### Database Scaling

- Enable connection pooling (already configured)
- Add read replicas for heavy read workloads
- Upgrade to higher-tier database plan

### Caching

- Increase Redis memory
- Add cache for frequently accessed repositories
- Implement CDN for static assets

---

## Support

- **Documentation**: [docs/](../docs/)
- **Issues**: https://github.com/yourusername/devintel/issues
- **Discussions**: GitHub Discussions

---

Last updated: 2026-02-12
