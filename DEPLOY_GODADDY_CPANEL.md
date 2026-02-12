# GoDaddy cPanel Deployment Guide

This project is now optimized for cPanel Passenger (Python App) and proxy/load-balancer environments.

## 1) Prepare Local Files

Required key files:
- `app_with_cookies.py`
- `passenger_wsgi.py`
- `requirements.txt`
- `templates/`
- `static/`

## 2) Create App in cPanel

1. Open `cPanel -> Setup Python App`.
2. Click `Create Application`.
3. Recommended values:
   - Python version: `3.11` (or latest available)
   - Application root: `instagram_video_downloader`
   - Application URL: your domain/subdomain
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
4. Click `Create`.

## 3) Upload Project

Upload the project into the app root (`instagram_video_downloader`) using File Manager, Git Version Control, or SSH.

## 4) Install Dependencies

In cPanel Terminal or SSH:

```bash
cd ~/instagram_video_downloader
source <cpanel_venv_path>/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If your host provides a pre-generated venv path in Python App UI, use that exact path.

## 5) Configure Environment Variables

In `Setup Python App -> Environment variables`, add:

- `ADMIN_USERNAME=your-admin-username`
- `ADMIN_PASSWORD=your-strong-admin-password`
- `FLASK_SECRET_KEY=long-random-secret-value`
- `MAX_DOWNLOAD_WORKERS=4`
- `MAX_QUEUED_JOBS=200`
- `DOWNLOAD_TIMEOUT_SECONDS=480`

Then click `Restart` in Python App UI.

## 6) Verify After Restart

Open:
- `/api/health` -> should return JSON `{"status":"ok"}`
- `/api/ready` -> should return worker/queue readiness JSON
- `/admin/login` -> admin login page
- `/admin` -> admin dashboard page after login

## 7) cPanel Performance Notes

- Keep `MAX_DOWNLOAD_WORKERS` moderate (2-4) on shared hosting.
- Large video processing is CPU/network heavy; avoid very high worker counts.
- `analytics.db` is local SQLite; keep regular backup.

## 8) Security Checklist

- Set strong `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
- Set strong `FLASK_SECRET_KEY`.
- Keep `cookies.txt` private and never expose in public web path.
- Restrict `/admin` access with strong credentials.

## 9) Troubleshooting

### `ModuleNotFoundError`
Re-activate app virtualenv and reinstall `requirements.txt`.

### 500 errors after deploy
Check cPanel Passenger error logs and app logs. Restart app from cPanel.

### Slow downloads
Reduce concurrent usage and keep `MAX_DOWNLOAD_WORKERS` low.

## 10) Optional External Load Balancer

GoDaddy shared cPanel usually does not provide true server-side load balancing across multiple app instances.

If you move to VPS/Kubernetes later:
- run multiple gunicorn instances
- put Nginx/HAProxy in front
- route health checks to `/api/ready`
- keep `ProxyFix` enabled (already added)
