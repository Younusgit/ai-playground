# 🎮 AI Playground

> Multi-model AI Chat Platform — fully manageable from Android + Termux

**Features:** OpenAI, Anthropic, Google Gemini, Groq, Together AI • Streaming responses • User auth • Daily limits • Telegram Admin Bot • Deploy on Render + Supabase

---

## 📁 Project Structure

```
ai-playground/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/routes/
│   │   ├── auth.py               # Login, Register, JWT
│   │   ├── chat.py               # Streaming AI chat
│   │   ├── models.py             # List models
│   │   ├── admin.py              # Admin-only endpoints
│   │   └── usage.py              # Usage stats
│   ├── services/
│   │   ├── database.py           # PostgreSQL connection pool
│   │   └── ai_service.py         # Multi-provider AI calls
│   └── middleware/
│       └── rate_limiter.py       # IP-based rate limiting
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Chat.jsx          # Main chat UI
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── bot/
│   └── admin_bot.py              # Telegram Admin Bot
├── migrations/
│   └── 001_initial_schema.sql    # Database schema
├── scripts/
│   ├── start.sh                  # Start API + Bot
│   ├── deploy.sh                 # Push to GitHub → Render
│   ├── update.sh                 # Pull updates
│   ├── backup.sh                 # Backup database
│   └── migrate.sh                # Run SQL migrations
├── render.yaml                   # Render deployment config
└── setup.sh                      # One-command Termux setup
```

---

## 📱 TERMUX SETUP (Android Phone)

### Step 1 — Install Termux

Download **Termux** from F-Droid (NOT Play Store):
👉 https://f-droid.org/packages/com.termux/

### Step 2 — Initial Termux config

Open Termux and run:

```bash
# Allow storage access
termux-setup-storage

# Update packages
pkg update -y && pkg upgrade -y
```

### Step 3 — Clone project

```bash
# Install git first
pkg install git -y

# Clone your repo (after you push to GitHub)
git clone https://github.com/YOUR_USERNAME/ai-playground.git
cd ai-playground
```

### Step 4 — One-command setup

```bash
bash setup.sh
```

This installs: Python, pip, Node.js, git, all dependencies, and creates shortcut scripts.

### Step 5 — Configure environment

```bash
nano backend/.env
```

Fill in these values:

```env
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
JWT_SECRET=make-this-very-long-random-string-123456
ADMIN_EMAILS=your@email.com
TELEGRAM_BOT_TOKEN=123456:ABCdefGHI...
TELEGRAM_ADMIN_CHAT_ID=123456789
PORT=8000
```

### Step 6 — Run database migrations

```bash
bash scripts/migrate.sh
```

### Step 7 — Start everything

```bash
# Start API + Bot together
bash scripts/start.sh

# OR start separately (in different Termux sessions):
bash scripts/start.sh api    # Session 1
bash scripts/start.sh bot    # Session 2
```

---

## 🗄️ SUPABASE SETUP

### 1. Create project

1. Go to https://supabase.com
2. Click **New Project**
3. Choose name, password, region
4. Wait for project to be ready (~2 min)

### 2. Get Database URL

- Dashboard → **Settings** → **Database**
- Copy **Connection String** (URI format)
- Replace `[YOUR-PASSWORD]` with your project password

```
postgresql://postgres:YOUR_PASSWORD@db.PROJECTID.supabase.co:5432/postgres
```

### 3. Run migrations

Paste migration SQL directly in Supabase:
- Dashboard → **SQL Editor** → New query
- Paste contents of `migrations/001_initial_schema.sql`
- Click **Run**

OR from Termux (after setting DATABASE_URL):

```bash
bash scripts/migrate.sh
```

---

## 🤖 TELEGRAM BOT SETUP

### 1. Create bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Choose name and username
4. Copy the **token** → put in `TELEGRAM_BOT_TOKEN`

### 2. Get your Chat ID

1. Open Telegram → search **@userinfobot**
2. Send `/start`
3. Copy your **Id** → put in `TELEGRAM_ADMIN_CHAT_ID`

### 3. Get Admin JWT Token

After starting the API, login with your admin account and copy the JWT token. Set it as:

```env
ADMIN_JWT_TOKEN=eyJhbGciOiJIUzI1NiIs...
```

### 4. Bot Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show admin panel | `/start` |
| `/stats` | View all statistics | `/stats` |
| `/models` | List & toggle models | `/models` |
| `/apikeys` | View API keys | `/apikeys` |
| `/health` | API health check | `/health` |
| `/users` | List users | `/users` |
| `/addkey` | Add API key | `/addkey openai:sk-xxxx` |
| `/delkey` | Delete API key | `/delkey openai` |
| `/ban` | Ban a user | `/ban user-uuid-here` |
| `/unban` | Unban a user | `/unban user-uuid-here` |
| `/setlimit` | Set daily limit | `/setlimit user-id:100` |

---

## 🚀 RENDER DEPLOYMENT

### 1. Push to GitHub

```bash
# From Termux
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ai-playground.git
git push -u origin main
```

### 2. Deploy on Render

1. Go to https://render.com
2. Click **New** → **Blueprint**
3. Connect your GitHub repo
4. Render reads `render.yaml` automatically
5. Add environment variables in Render dashboard:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `ADMIN_EMAILS`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_ADMIN_CHAT_ID`
   - `API_URL` (your Render API URL, for the bot)
   - `ADMIN_JWT_TOKEN`

### 3. Deploy frontend (Netlify — free)

```bash
cd frontend
npm run build
# Upload the dist/ folder to netlify.com/drop
```

OR connect Netlify to your GitHub repo with:
- Build command: `npm run build`
- Publish directory: `dist`
- Environment variable: `VITE_API_URL=https://your-api.onrender.com`

---

## 🔧 DAILY MANAGEMENT (Termux Commands)

```bash
# Start everything
bash scripts/start.sh

# Deploy after changes
bash scripts/deploy.sh "Added new feature"

# Pull updates from GitHub
bash scripts/update.sh

# Backup database
bash scripts/backup.sh

# Run new migrations
bash scripts/migrate.sh
```

---

## 🔑 ADDING AI PROVIDERS

After deploying, add API keys via Telegram bot:

```
/addkey openai:sk-proj-xxxxxxxxxxxx
/addkey anthropic:sk-ant-xxxxxxxxxxxx
/addkey google:AIzaxxxxxxxxxxxx
/addkey groq:gsk_xxxxxxxxxxxx
/addkey together:xxxxxxxxxxxx
```

Then enable/disable models via `/models` command.

### Where to get API keys

| Provider | URL |
|----------|-----|
| OpenAI | https://platform.openai.com/api-keys |
| Anthropic | https://console.anthropic.com |
| Google Gemini | https://aistudio.google.com/app/apikey |
| Groq (Free!) | https://console.groq.com |
| Together AI | https://api.together.xyz |

---

## 🛡️ SECURITY BEST PRACTICES

1. **JWT Secret** — use a long random string (32+ characters)
2. **Admin emails** — only your email in `ADMIN_EMAILS`
3. **Database** — never expose DATABASE_URL publicly
4. **HTTPS** — Render provides SSL automatically
5. **Rate limiting** — built-in IP-based rate limiter (60 req/min)
6. **Daily limits** — per-user message limits via admin bot
7. **Bot security** — admin bot only responds to `TELEGRAM_ADMIN_CHAT_ID`

Generate secure JWT secret in Termux:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🌐 API ENDPOINTS

```
POST  /api/auth/register     Register new user
POST  /api/auth/login        Login
GET   /api/auth/me           Current user info

GET   /api/models/           List enabled models
POST  /api/chat/stream       Stream AI response (SSE)
GET   /api/chat/history      User chat history

GET   /api/usage/my          User usage stats

GET   /api/admin/stats       Platform statistics
GET   /api/admin/users       All users
POST  /api/admin/api-keys    Add API key
DELETE /api/admin/api-keys/{provider}
POST  /api/admin/models/toggle
POST  /api/admin/users/ban
POST  /api/admin/users/unban
POST  /api/admin/limits

GET   /health                Health check
GET   /docs                  API documentation (Swagger)
```

---

## 🔄 WORKFLOW (Android-First)

```
Android Phone (Termux)
    │
    ├── Edit code → nano / vim
    ├── Git commit → git add . && git commit
    ├── Deploy → bash scripts/deploy.sh
    │
    └── Manage via Telegram Bot
            ├── /stats     → see metrics
            ├── /addkey    → add API keys
            ├── /models    → enable/disable models
            ├── /ban       → ban users
            └── /health    → check if API is up
```

---

## 🐛 TROUBLESHOOTING

**API won't start:**
```bash
# Check Python version
python --version   # Need 3.10+

# Check .env is loaded
cat backend/.env

# Check database connection
psql $DATABASE_URL -c "SELECT 1"
```

**Bot not responding:**
```bash
# Check token
echo $TELEGRAM_BOT_TOKEN

# Check admin ID matches
echo $TELEGRAM_ADMIN_CHAT_ID
```

**Models not showing:**
- Check API keys added: `/apikeys` in bot
- Check models enabled: `/models` in bot
- Verify migration ran: SQL Editor in Supabase

**Render deploy fails:**
- Check environment variables set in Render dashboard
- Check build logs in Render dashboard
- Verify requirements.txt has all packages

---

## 📊 SUPPORTED MODELS (Default)

| Model | Provider | Speed |
|-------|----------|-------|
| GPT-4o | OpenAI | Fast |
| GPT-4o Mini | OpenAI | Very Fast |
| GPT-3.5 Turbo | OpenAI | Ultra Fast |
| Claude 3.5 Sonnet | Anthropic | Fast |
| Claude 3 Haiku | Anthropic | Very Fast |
| Gemini 1.5 Pro | Google | Fast |
| Gemini 1.5 Flash | Google | Very Fast |
| Llama 3.1 70B | Groq | Ultra Fast (Free) |
| Mixtral 8x7B | Groq | Ultra Fast (Free) |
| Llama 3.1 405B | Together | Fast |

---

Made with ❤️ for Android-first development
