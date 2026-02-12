# DevIntel - Demo Video Script

## Video Length: 3-4 minutes

---

## Opening (0:00 - 0:20)

**[Screen: DevIntel landing page with logo]**

**Voiceover:**
> "Hi, I'm [Your Name], and today I'm going to show you DevIntel - an AI-powered developer productivity platform that I built from scratch."

**[Quick montage of screens: Dashboard → Chat → Code]**

> "DevIntel lets you connect your GitHub repositories and chat with your code using AI. It's like having ChatGPT, but for your specific codebase."

---

## Problem Statement (0:20 - 0:40)

**[Screen: Show complex codebase with lots of files]**

**Voiceover:**
> "When you join a new team or work with a large codebase, understanding how everything works can take days or even weeks."

**[Screen: Developer scrolling through docs, searching code]**

> "You spend hours reading documentation, grepping through files, and trying to piece together how components interact."

**[Screen transition: DevIntel logo appears]**

> "DevIntel solves this problem."

---

## Core Feature Demo (0:40 - 2:00)

### 1. Connect Repository (0:40 - 1:00)

**[Screen: Login with GitHub OAuth]**

**Voiceover:**
> "First, you authenticate with GitHub OAuth. This is completely secure - DevIntel never stores your GitHub password."

**[Screen: Dashboard with 'Add Repository' button]**

**Click: Add Repository**

**Type in modal:** `your-username/your-repo`

**Voiceover:**
> "Then you can connect any of your GitHub repositories - public or private."

**[Screen: Indexing progress bar appears]**

> "DevIntel clones the repository and indexes it using vector embeddings. This takes about 30 seconds for a typical project."

**[Progress bar completes: "✓ Indexing complete - 10,247 chunks indexed"]**

---

### 2. Chat with Code (1:00 - 1:40)

**[Screen: AI Chat interface opens]**

**Voiceover:**
> "Now here's where the magic happens. I can ask questions about my code, and the AI understands the context."

**[Type in chat]:**
> "What does the authentication flow look like?"

**[AI response streams in]:**
> "The authentication flow uses GitHub OAuth 2.0. Here's how it works:
> 
> 1. User clicks 'Login with GitHub'
> 2. Redirected to GitHub authorization page
> 3. GitHub calls back to `/auth/callback` with code
> 4. Backend exchanges code for access token
> 5. JWT token generated and returned to client
>
> I can see this implemented in `app/api/v1/auth.py` lines 45-78."

**Voiceover:**
> "Notice how it not only explains the flow but also tells me exactly where in the code this is implemented."

**[Type in chat]:**
> "Show me how the RAG pipeline processes code chunks"

**[AI response streams]:**
> "The RAG pipeline works in three stages:
> [... detailed explanation ...]"

**Voiceover:**
> "The responses are accurate because DevIntel uses Retrieval Augmented Generation - it actually searches your codebase's vector embeddings before generating answers."

---

### 3. Quick Feature Highlight (1:40 - 2:00)

**[Screen: Quick cuts showing different features]**

**Voiceover:**
> "DevIntel also shows you your indexed repositories, chat history, and provides semantic code search - meaning you can search by what the code does, not just what it says."

---

## Technical Highlights (2:00 - 2:40)

**[Screen: Architecture diagram]**

**Voiceover:**
> "Now let me show you what makes this impressive from an engineering perspective."

**[Highlight backend]**
> "The backend uses FastAPI with async Python for high performance. PostgreSQL with the pgvector extension handles vector embeddings."

**[Highlight services]**
> "Background jobs like indexing run on Celery workers, so the API stays responsive."

**[Show security badges]**
> "Security is production-grade: OWASP compliant headers, input validation, JWT authentication, and comprehensive test coverage of over 80%."

**[Show CI/CD pipeline]**
> "Full CI/CD pipeline with automated testing, linting, and Docker builds on every commit."

**[Screen: Test results showing 39 passing tests]**

> "And speaking of testing - the entire application has comprehensive unit and integration tests."

---

## Production Readiness (2:40 - 3:00)

**[Screen: deployment options]**

**Voiceover:**
> "DevIntel is fully production-ready. I've created deployment guides for Railway, Render, DigitalOcean, AWS, and self-hosted VPS."

**[Screen: Monitoring dashboard (mock)]**

> "It includes error tracking with Sentry, structured logging, health checks, and automated backups."

**[Screen: Documentation pages]**

> "Complete documentation including security guidelines, deployment procedures, and contribution guidelines."

---

## Call to Action (3:00 - 3:20)

**[Screen: GitHub repo with README]**

**Voiceover:**
> "The entire project is open source under the MIT license."

**[Screen: Show GitHub Stats - stars, forks, etc.]**

> "Check out the repository at github.com/[your-username]/devintel. I'd love to hear your feedback!"

**[Screen: Your contact info / portfolio]**

> "I'm [Your Name], and I build production-ready full-stack applications. You can find me on LinkedIn, GitHub, or at [your-website].com."

**[Screen: DevIntel logo fades in]**

> "Thanks for watching!"

---

## Recording Tips

### Before Recording

1. **Clean your repository**
   - Remove any sensitive data
   - Use a demo repository with clean code
   - Ensure indexing completes successfully

2. **Prepare your demo environment**
   - Fresh database
   - Pre-indexed a demo repository
   - Test all flows work

3. **Script your questions**
   - Write out chat questions that show best results
   - Test responses beforehand
   - Have backup questions ready

### Recording Best Practices

1. **Screen Recording**
   - Use OBS Studio or Loom
   - 1080p resolution minimum
   - 30 FPS
   - Hide desktop icons
   - Close unnecessary apps

2. **Audio**
   - Use external microphone if possible
   - Record in quiet room
   - Test audio levels first
   - No background music (keeps it professional)

3. **Pacing**
   - Speak clearly and not too fast
   - Pause between sections
   - Don't rush through code/terminal output

4. **Editing**
   - Speed up slow parts (indexing, loading) to 2x
   - Add zoom-ins for important parts
   - Use on-screen text for key points
   - Add captions (increases engagement)

### On-Screen Text Additions

- Repository indexing: "Processing 10,247 code chunks"
- Security: "OWASP Top 10 Compliant"
- Testing: "80%+ Test Coverage"
- Tech Stack: "FastAPI • PostgreSQL • React • OpenAI"

---

## Alternative: Short Version (60 seconds)

For LinkedIn/Twitter:

1. **Problem** (10s): "Understanding unfamiliar codebases is hard"
2. **Solution** (15s): "Connect GitHub repo, ask questions"
3. **Demo** (25s): Show one good chat interaction
4. **Tech** (10s): "FastAPI + PostgreSQL + RAG + 80% test coverage"
5. **CTA** (5s): "Link in bio!"

---

## Distribution Channels

- **YouTube**: Full 3-4 minute version
- **LinkedIn**: 60-90 second highlight
- **Twitter/X**: 30-60 second teaser
- **Portfolio Website**: Full version embedded
- **GitHub README**: Embed YouTube video

---

## Metrics to Track

After posting:
- Views
- Engagement (likes, comments, shares)
- Click-through to repo
- GitHub stars increase
- Job inquiries

---

Last updated: 2026-02-12
