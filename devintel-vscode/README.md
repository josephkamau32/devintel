# DevIntel AI — VS Code Extension

> **AI-powered code intelligence directly in your editor** — RAG-based chat, autonomous code review, and semantic search powered by your indexed GitHub repositories.

[![VS Code Version](https://img.shields.io/badge/VS%20Code-%5E1.85.0-blue.svg)](https://code.visualstudio.com/)

---

## Features

### 🤖 Sidebar AI Chat
Click the DevIntel icon in the Activity Bar to open the chat panel. Select any indexed repository from the dropdown and ask natural-language questions about your codebase:

- *"Explain the overall architecture"*
- *"Show me all API endpoints and their purposes"*
- *"Find potential bugs in the auth module"*

Responses are streamed in real-time with per-message token cost tracking.

### 👁️ Review Current File
Right-click in any editor → **DevIntel: Review Current File** (or run from the Command Palette). DevIntel will analyse the active file for bugs, security issues, and improvement opportunities using your indexed codebase as context.

### 💬 Ask AI (Command Palette)
`Ctrl+Shift+P` → **DevIntel: Ask AI** — focuses the sidebar chat panel instantly.

---

## Requirements

- A running [DevIntel API](https://github.com/josephkamau32/devintel) instance
- A JWT access token from your DevIntel account settings

---

## Extension Settings

| Setting | Description | Default |
|---|---|---|
| `devintel.apiBaseUrl` | Base URL of your DevIntel backend | `http://localhost:8000` |

The API token is stored securely in VS Code's **Secret Storage** (OS keychain).

---

## Getting Started

1. Install the extension
2. Run **DevIntel: Set API URL** to point it at your backend (if not localhost)
3. Run **DevIntel: Set API Token** and paste your JWT access token
4. Click the ⚡ DevIntel icon in the Activity Bar
5. Select an indexed repository and start asking questions!

---

## Commands

| Command | Description |
|---|---|
| `DevIntel: Ask AI` | Open / focus the sidebar chat |
| `DevIntel: Review Current File` | Analyse the active editor file |
| `DevIntel: Set API Token` | Store your JWT token securely |
| `DevIntel: Set API Base URL` | Configure the API endpoint |

---

## Privacy

All queries are sent to **your own** DevIntel backend. No data is sent to any third-party service by the extension itself.

---

## License

MIT © DevIntel AI
