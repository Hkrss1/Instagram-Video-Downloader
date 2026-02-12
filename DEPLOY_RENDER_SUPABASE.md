# Free Deployment: Render + Supabase (Postgres)

This guide deploys your app for free with persistent database support.

## 1) Push code to GitHub

Create/update a GitHub repo with this project.

## 2) Create Postgres on Supabase (free)

1. Go to Supabase and create a new project.
2. Open `Project Settings -> Database`.
3. Copy the connection string URI (Postgres URL).
4. Replace `[YOUR-PASSWORD]` with your DB password.

## 3) Create web service on Render

1. Go to Render -> New -> Web Service.
2. Connect your GitHub repo.
3. Render should detect `render.yaml` automatically.
4. Create service.

## 4) Set required environment variables on Render

In Render service settings, set:

- `DATABASE_URL` = Supabase Postgres URI
- `ADMIN_USERNAME` = your admin username
- `ADMIN_PASSWORD` = strong password
- `YTDLP_COOKIES_B64` = base64 of your exported YouTube `cookies.txt` (recommended)

Optional tuneables:
- `MAX_DOWNLOAD_WORKERS=4`
- `MAX_QUEUED_JOBS=200`
- `DOWNLOAD_TIMEOUT_SECONDS=480`

`FLASK_SECRET_KEY` is generated automatically from `render.yaml`.

## 5) Deploy and verify

After deploy:

- `https://<your-service>.onrender.com/api/health` -> `{"status":"ok"}`
- `https://<your-service>.onrender.com/api/ready` -> readiness JSON
- `https://<your-service>.onrender.com/admin/login` -> admin login page

## 6) Admin login

Use `ADMIN_USERNAME` + `ADMIN_PASSWORD` you configured in Render.

## 7) Notes for free plans

- Render free services may sleep after inactivity.
- First request after sleep can be slow.
- Heavy simultaneous downloads can hit free-tier limits.

## 8) If DB connection fails

- Confirm `DATABASE_URL` format is valid Postgres URI.
- Ensure Supabase project is active.
- Re-check DB password inside URI.

## 8b) If YouTube shows \"Sign in to confirm you're not a bot\"

Render/shared cloud IPs are often challenged by YouTube. Configure server-side cookies:

1. Export YouTube cookies (`cookies.txt`) from a logged-in browser.
2. Convert to base64:

```bash
python -c "import base64; print(base64.b64encode(open('cookies.txt','rb').read()).decode())"
```

3. Set Render env var:
- `YTDLP_COOKIES_B64=<that_base64_string>`

4. Redeploy.

Alternative (less recommended): set raw `YTDLP_COOKIES_TXT` with full cookies text.

## 9) Security checklist

- Do not hardcode admin credentials in source.
- Keep `ADMIN_PASSWORD` strong.
- Keep `FLASK_SECRET_KEY` private.

## 10) One-click migration from `analytics.db` to Supabase Postgres

If you already have local analytics data, run this once locally:

```bash
python migrate_analytics_to_postgres.py --database-url "YOUR_SUPABASE_DATABASE_URL"
```

Or with env var:

```bash
set DATABASE_URL=YOUR_SUPABASE_DATABASE_URL
python migrate_analytics_to_postgres.py
```

Notes:
- Script is idempotent (`ON CONFLICT (id) DO NOTHING`), so re-running is safe.
- It also updates Postgres sequence after insert.
- Default SQLite source file is `analytics.db`.
