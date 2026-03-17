# GDriveGenie

Self-hosted unified dashboard that aggregates multiple Google Drive accounts into a single storage pool. Every upload automatically routes to the account with the most available space — no manual management, no paid tier.

> **Runs entirely on your local machine. Your files stay in your own Google Drive accounts.**

---

## Why GDriveGenie?

Google gives every account **15 GB free**. GDriveGenie lets you combine as many accounts as you want into one unified interface — effectively giving you N × 15 GB of free cloud storage. Add more accounts at any time without changing any configuration.

---

## Features

- **Unified storage pool** — one dashboard for all your Drive accounts
- **Smart upload routing** — Least-Used-Space strategy picks the best account on every upload
- **Folder navigation** — full hierarchy, breadcrumbs, grid & list views, search, filters
- **Drag-to-folder** — drag a file and drop it into any folder from a slide-in panel
- **Shared with me** — browse and download files others have shared with your accounts
- **Trash management** — delete goes to Drive trash; restore or permanently delete anytime
- **Analytics** — storage by account, file type charts, weekly upload activity
- **Profile** — display name, bio, avatar stored in your own Drive
- **Secure** — bcrypt-hashed PIN, httponly JWT cookie, OAuth tokens encrypted at rest (Fernet)
- **No .env needed** — secrets are stored directly in the local SQLite database
- **Dark / light theme**
- **100% open source, $0 cost**

---

## Quick Start

**Prerequisites:** Python 3.10+, Node.js 18+, at least one Google account

### 1. Clone

```bash
git clone https://github.com/saimon4u/GDriveGenie.git
cd GDriveGenie
```

### 2. Google OAuth credentials

You only need **one Google Cloud project** and one credentials file — no matter how many Drive accounts you add.

1. Go to [Google Cloud Console](https://console.cloud.google.com) → create a new project
2. Enable **Google Drive API**
3. Create an OAuth consent screen → choose **External**, fill in any app name, and add **all Google accounts you want to connect** as test users
4. Create credentials → **OAuth client ID → Web application** → add `http://localhost:8000/api/auth/callback` as an authorized redirect URI → download JSON
5. Save the file as `config/credentials.json`

> **About the `config/` folder:** It is tracked in git as an empty placeholder (via `.gitkeep`) so it exists right after cloning. Its contents are listed in `.gitignore` — your credentials are **never** accidentally committed. Just drop the downloaded JSON file in as `credentials.json`.

### 3. Install & set up

```bash
pip install -r backend/requirements.txt
python backend/scripts/generate_secrets.py
```

Enter a PIN when prompted — your PIN hash, JWT secret, and encryption key are written directly to `backend/gdriveGenie.db`. No `.env` file needed.

### 4. Start the servers

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

### 5. Connect your accounts

Open [http://localhost:3000](http://localhost:3000), log in with your PIN, navigate to **Settings**, and click **Connect another account**. Google will show the account chooser — pick any Google account you want to add to the pool.

That's it — start uploading at [http://localhost:3000/dashboard](http://localhost:3000/dashboard).

---

## Docker

Docker Compose is the easiest way to run GDriveGenie without installing Python or Node.js locally.

**Prerequisites:** Docker and Docker Compose

### 1. Place your credentials

Save your downloaded Google OAuth JSON file as `config/credentials.json`. The `config/` folder already exists in the repo — just drop the file in.

### 2. Build the images

```bash
docker compose build
```

### 3. Initialize secrets (first run only)

```bash
docker compose run --rm backend python scripts/generate_secrets.py
```

Enter a PIN when prompted. Secrets are written to the `gdriveGenie_data` persistent Docker volume.

### 4. Start the stack

```bash
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000). View logs anytime with `docker compose logs -f`.

### Persistent data

| Data | Storage |
|------|---------|
| SQLite database | `gdriveGenie_data` named Docker volume |
| Google credentials | `./config/credentials.json` (bind-mounted read-only) |

### Environment variables

All variables have sensible defaults for local use. Override them in `docker-compose.yml` for custom deployments.

| Variable | Default | Purpose |
|----------|---------|---------|
| `FRONTEND_URL` | `http://localhost:3000` | Allowed CORS origin for the backend |
| `BACKEND_URL` | `http://localhost:8000` | Public URL used to build the OAuth callback URI |
| `DB_PATH` | `backend/gdriveGenie.db` | Path to the SQLite database file |
| `CONFIG_DIR` | `config/` | Directory containing `credentials.json` |

> **`BACKEND_URL` is important:** GDriveGenie uses it to construct the OAuth redirect URI sent to Google. The default works for local and Docker deployments. If you put the backend behind a reverse proxy or a different hostname, update this value — and add the new callback URL to your Google Cloud Console authorized redirect URIs.

---

## Adding more storage

Go to **Settings** and click **Connect another account** — no file changes, no restart needed. Make sure the new Google account is added as a test user on the OAuth consent screen first. Each free Google account adds 15 GB to your pool.

---

## Security notes

- `config/credentials.json` and `backend/gdriveGenie.db` contain sensitive data — keep them out of version control (already covered by `.gitignore`) and back them up securely.
- OAuth refresh tokens are encrypted with Fernet (AES-128-CBC) before being stored. The encryption key lives in the database alongside the PIN hash and JWT secret.
- If you expose GDriveGenie over the internet, put it behind a reverse proxy with HTTPS and update both `FRONTEND_URL` and `BACKEND_URL` accordingly.

---

## Tech stack

| Layer | Tech |
|-------|------|
| Backend | Python · FastAPI · SQLite · Google Drive API v3 |
| Frontend | Next.js (App Router) · Tailwind CSS |

---

## Full setup guide

See [http://localhost:3000/docs](http://localhost:3000/docs) once the app is running, or read `frontend/app/docs/page.tsx` directly.

---

## License

MIT
