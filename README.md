# IT Support AI Agent

An AI agent that takes natural-language IT support requests and carries them out on a mock admin panel — navigating the browser like a human would, using **Gemini** as the LLM and **browser-use** for browser automation.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│  User / Slack                                              │
│  "reset password for john@company.com"                     │
└────────────────┬───────────────────────────────────────────┘
                 │ HTTP POST /api/agent  (or Slack mention)
                 ▼
┌────────────────────────────────────────────────────────────┐
│  FastAPI Backend  (Render)                                 │
│                                                            │
│  ┌──────────────────┐    ┌───────────────────────────┐    │
│  │  Mock IT Admin   │    │  AI Agent                 │    │
│  │  Panel (Jinja2)  │    │                           │    │
│  │                  │    │  1. Receives NL task       │    │
│  │  /users          │◄───│  2. Gemini decides steps  │    │
│  │  /users/create   │    │  3. browser-use controls  │    │
│  │  /reset-password │    │     a real Chromium       │    │
│  │  /licenses       │    │  4. Navigates, clicks,    │    │
│  │  /toggle-status  │    │     fills forms           │    │
│  │  /audit-log      │    │  5. Returns result        │    │
│  └──────────────────┘    └───────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
                 │ result
                 ▼
┌────────────────────────────────────────────────────────────┐
│  React Chat UI  (Vercel)          Slack Bot                │
│  Type task → see result           @ITAgent <task>          │
└────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| LLM | Gemini 2.0 Flash | Free tier, fast, multimodal |
| Browser automation | browser-use | LLM-native; Gemini sees the page and decides what to click — no DOM selectors or API shortcuts |
| Admin panel | FastAPI + Jinja2 | Simple, functional, no frontend framework needed for the panel itself |
| State | In-memory Python dict | Keeps the demo self-contained; swap with a real DB for production |
| Agent trigger | REST API + Slack Socket Mode | Both call the same `run_agent()` function |

---

## 📁 Project Structure

```
it-agent/
├── backend/
│   ├── admin_panel/
│   │   ├── database.py        # In-memory user store + audit log
│   │   ├── routes.py          # All admin panel pages (FastAPI routes)
│   │   └── templates/         # Jinja2 HTML templates
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── users.html
│   │       ├── create_user.html
│   │       ├── reset_password.html
│   │       ├── licenses.html
│   │       ├── toggle_status.html
│   │       └── audit_log.html
│   ├── agent/
│   │   └── agent.py           # browser-use + Gemini agent
│   ├── slack_bot/
│   │   └── bot.py             # Slack Socket Mode bot
│   ├── main.py                # FastAPI app entry point
│   ├── run_agent.py           # CLI runner for local testing
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # React chat UI
│   │   └── index.js
│   ├── public/index.html
│   ├── package.json
│   └── .env.example
├── render.yaml                # Render deployment config
└── vercel.json                # Vercel deployment config
```

---

## 🚀 Local Setup

### 1. Clone & set up backend

```bash
git clone <your-repo>
cd it-agent/backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium  # Linux only
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Start the backend

```bash
uvicorn main:app --reload --port 8000
```

Visit: http://localhost:8000 → you'll see the admin panel.

### 4. Test the agent from CLI

```bash
python run_agent.py "reset password for john@company.com to NewPass@99"
python run_agent.py "create user Alice Brown, alice@company.com, Engineer, Engineering"
python run_agent.py "assign GitHub license to sarah@company.com"
python run_agent.py "check if alice@company.com exists, if not create them, then assign Figma"
```

This opens a **visible browser** window so you can watch the agent work.

### 5. Start the React frontend

```bash
cd ../frontend
cp .env.example .env          # REACT_APP_API_URL=http://localhost:8000
npm install
npm start                     # Opens http://localhost:3000
```

---

## ☁️ Deployment

### Backend → Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo — Render reads `render.yaml` automatically
4. In the service's Environment tab, add:
   - `GEMINI_API_KEY` = your key
   - `ADMIN_PANEL_URL` = `https://it-agent-backend.onrender.com`
5. Deploy

> ⚠️ **Important:** Render free tier spins down after inactivity. The first request may take ~30s to wake up.

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → New Project → Import repo
2. Set **Root Directory** to `frontend`
3. Add environment variable:
   - `REACT_APP_API_URL` = `https://it-agent-backend.onrender.com`
4. Deploy

---

## 💬 Slack Bot Setup (Optional)

1. Go to https://api.slack.com/apps → Create New App → From Scratch
2. Enable **Socket Mode** (Settings → Socket Mode) → generate App-Level Token (`connections:write` scope) → this is `SLACK_APP_TOKEN`
3. Go to **OAuth & Permissions** → add Bot Token Scopes:
   - `app_mentions:read`, `chat:write`, `channels:history`, `im:history`, `im:write`
4. Go to **Event Subscriptions** → enable → subscribe to:
   - `app_mention`, `message.im`
5. Install to workspace → copy **Bot User OAuth Token** → this is `SLACK_BOT_TOKEN`
6. Add both tokens to your `.env` or Render environment variables
7. Invite the bot to a channel: `/invite @ITAgent`
8. Use it: `@ITAgent reset password for john@company.com`

---

## 🧪 Example Tasks to Demo

| Task | Type |
|---|---|
| `reset password for john@company.com to NewPass@99` | Simple |
| `create user Alice Brown, alice@company.com, Engineer, Engineering` | Simple |
| `assign GitHub license to sarah@company.com` | Simple |
| `deactivate mike@company.com` | Simple |
| `check if alice@company.com exists, if not create them, then assign Figma license` | Multi-step conditional |
| `list all users` | Read-only |

---

## 🤖 How the Agent Works

1. **Natural language in** → `run_agent("reset password for john@company.com")`
2. **Gemini reads the system prompt** which tells it what pages exist and how forms work
3. **browser-use launches Chromium** and gives Gemini a live view of the page
4. **Gemini decides**: "I should go to `/users/reset-password`, type the email, fill the new password, click submit"
5. **browser-use executes** each action (navigate, click, type, submit)
6. **Gemini verifies** the success message on screen
7. **Result returned** to the API / Slack / Chat UI

No DOM selectors. No API shortcuts. The agent reads and interacts with the UI exactly like a human would.
