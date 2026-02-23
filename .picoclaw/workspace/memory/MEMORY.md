# 🧠 Long-term Memory (N8N & Database Protocol)

## 🛠 1. Core Execution Protocol (Critical)
- **Initialization**: Always read the `.env` file **first** before any operations to load credentials and project context.
- **Routing Logic**:
    - **Local Database** ➡️ Use **Local Postgres (OpenClaw)** tools.
    - **Remote / Online Database** ➡️ Use **Supabase** tools.
    - **Opencode** ➡️ when user ask opencode operations, always use "opencode run 'customer request text'". if customer ask opencode to run tasks under specific agent, always use "opencode  --agent 'agent name' run 'customer request text'"
    - **Third-Party Services** (Tavily, Cloudflare, Vercel, etc.) ➡️ Use their specific MCP/skills/tools.
- **Session Management**: In any conversation, when a new instruction arrives, identify the relationship between the new instruction and the current context. If the relevance is high, maintain the existing session and model pool. If unrelated, start a new session.

---

## 💾 2. Database Operations

### A. Remote Database (Supabase)
- **Primary Project ID**: `nguwuoiivcqldbwkowwv` (N8N Project)
- **DDL (Schema)**: `apply_migration(project_id, name, query)`
- **DML (Data)**: `execute_sql(project_id, query)`
- **Validation**: `list_tables(project_id, schemas=["public"])` (Note: `schemas` must be an **array** `["public"]`).

### B. Local Database (OpenClaw/Postgres)
- **Target**: Local PostgreSQL instance managed via OpenClaw MCP.
- **Usage**: When the user specifies "local database" or "local storage," use the standard `postgres` MCP toolset.

---

## 🌐 3. Third-Party Skills & Web Control

### A. Service Integration
- **Tavily**: Use for advanced web search and AI-optimized research.
- **Cloudflare/Vercel**: Use corresponding MCP tools for deployment, DNS, or KV storage operations.
- **Web Search (General)**: If Brave API is missing, use Google Search patterns (see Section 4).

### B. Browser Control (OpenClaw Extension)
- **Connectivity**: Extension icon must be **Blue** (Connected).
- **Navigation**: Prefer `browser action=navigate` + `web_fetch(extractMode="text")`.
- **Error "tab not found"**: Indicates the Chrome extension is disconnected.

---

## 🔍 4. Specialized Search Patterns (Google)
Use `open -a "Google Chrome" "URL"` templates (replace `+` for spaces):
- **General**: `.../search?q=QUERY`
- **Images**: `...&tbm=isch` | **News**: `...&tbm=nws` | **Videos**: `...&tbm=vid` | **Books**: `...&tbm=bks`

---

## 📂 5. Workspace & Environment
- **Obsidian Vault**: `/Users/jiancao/Document/obsidian/study/openclaw`
- **Binary Path**: `/Users/jiancao/Downloads/picoclaw_Darwin_arm64/picoclaw` (Note: If running as a global command, use `picoclaw` after moving to `/usr/local/bin`).

---

## ⚠️ 6. Lessons Learned & Anti-Patterns
- **No REST for Schema**: Do not use Supabase REST API for `DROP/CREATE` tables; use `apply_migration`.
- **Parameter Strictness**: Ensure SQL queries are sanitized and MCP parameters (like arrays) are correctly typed.
- **Fallback**: If automated browser control fails (`ref is required`), fallback to direct URL fetching or manual navigation instructions.
---

## 🔄 consolidation_20260223_2004

**Consolidation Run**: 2026-02-23 12:04 UTC  
**Sessions Analyzed**: 3  
**Time Window**: Last 7 days

🦞 picoclaw - Personal AI Assistant v0.1.2

Usage: picoclaw <command>

Commands:
  onboard     Initialize picoclaw configuration and workspace
  agent       Interact with the agent directly
  auth        Manage authentication (login, logout, status)
  gateway     Start picoclaw gateway
  status      Show picoclaw status
  cron        Manage scheduled tasks
  migrate     Migrate from OpenClaw to PicoClaw
  skills      Manage skills (install, list, remove)
  version     Show version information
Analysis failed

---

---

## 🔄 consolidation_20260223_2004

**Consolidation Run**: 2026-02-23 12:04 UTC  
**Sessions Analyzed**: 1  
**Time Window**: Last 7 days

Analysis pending - AI service unavailable

---

---

## 🔄 consolidation_20260223_2007

**Consolidation Run**: 2026-02-23 12:07 UTC  
**Sessions Analyzed**: 1  
**Time Window**: Last 7 days

Analysis pending - AI service unavailable

---
