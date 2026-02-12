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

## 9) Security checklist

- Do not hardcode admin credentials in source.
- Keep `ADMIN_PASSWORD` strong.
- Keep `FLASK_SECRET_KEY` private.
