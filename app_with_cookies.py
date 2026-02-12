from flask import Flask, render_template, request, jsonify, send_file, Response, stream_with_context, g, session, redirect, url_for
from flask_cors import CORS
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import re
import base64
import atexit
import sqlite3
import logging
import secrets
import hmac
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urlunsplit
from io import BytesIO

import requests
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    import psycopg2
except Exception:
    psycopg2 = None

app = Flask(__name__)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = bool(int(os.environ.get('SESSION_COOKIE_SECURE', '0')))
app.permanent_session_lifetime = timedelta(seconds=int(os.environ.get('ADMIN_SESSION_SECONDS', '43200')))

youtube_jobs = {}
youtube_jobs_lock = threading.Lock()
YOUTUBE_JOB_TTL_SECONDS = 30 * 60
ANALYTICS_DB_PATH = os.path.join(os.getcwd(), 'analytics.db')
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
DB_FALLBACK_SQLITE = os.environ.get('DB_FALLBACK_SQLITE', '1') == '1'
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
MAX_DOWNLOAD_WORKERS = max(2, int(os.environ.get('MAX_DOWNLOAD_WORKERS', '4')))
DOWNLOAD_TIMEOUT_SECONDS = int(os.environ.get('DOWNLOAD_TIMEOUT_SECONDS', '480'))
MAX_QUEUED_JOBS = max(10, int(os.environ.get('MAX_QUEUED_JOBS', '200')))
youtube_executor = ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS, thread_name_prefix='yt-worker')
logger = logging.getLogger('video_downloader')
YTDLP_COOKIES_B64 = os.environ.get('YTDLP_COOKIES_B64', '').strip()
YTDLP_COOKIES_TXT = os.environ.get('YTDLP_COOKIES_TXT', '').strip()
_YTDLP_COOKIES_PATH = None
_YTDLP_COOKIES_LOCK = threading.Lock()


def _cleanup_ytdlp_cookies_file():
    global _YTDLP_COOKIES_PATH
    path = _YTDLP_COOKIES_PATH
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
    _YTDLP_COOKIES_PATH = None


def _ensure_ytdlp_cookies_file():
    global _YTDLP_COOKIES_PATH
    if _YTDLP_COOKIES_PATH and os.path.exists(_YTDLP_COOKIES_PATH):
        return _YTDLP_COOKIES_PATH

    with _YTDLP_COOKIES_LOCK:
        if _YTDLP_COOKIES_PATH and os.path.exists(_YTDLP_COOKIES_PATH):
            return _YTDLP_COOKIES_PATH

        raw = ''
        if YTDLP_COOKIES_TXT:
            raw = YTDLP_COOKIES_TXT
        elif YTDLP_COOKIES_B64:
            try:
                raw = base64.b64decode(YTDLP_COOKIES_B64).decode('utf-8')
            except Exception as exc:
                logger.warning("Failed to decode YTDLP_COOKIES_B64: %s", exc)
                return ''
        else:
            return ''

        try:
            fd, path = tempfile.mkstemp(prefix='yt_cookies_', suffix='.txt')
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
                f.write(raw)
            _YTDLP_COOKIES_PATH = path
            return _YTDLP_COOKIES_PATH
        except Exception as exc:
            logger.warning("Failed to create temporary yt-dlp cookies file: %s", exc)
            return ''


def _youtube_cookies_path():
    env_path = _ensure_ytdlp_cookies_file()
    if env_path and os.path.exists(env_path):
        return env_path
    if os.path.exists('cookies.txt'):
        return 'cookies.txt'
    return ''


atexit.register(_cleanup_ytdlp_cookies_file)


def _db_connect():
    if DATABASE_URL:
        if psycopg2 is None:
            raise RuntimeError("DATABASE_URL is set but psycopg2 is not installed")
        db_url = DATABASE_URL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        try:
            return psycopg2.connect(db_url), 'postgres'
        except Exception as exc:
            if not DB_FALLBACK_SQLITE:
                raise
            logger.warning("Postgres unavailable, falling back to SQLite: %s", exc)
    conn = sqlite3.connect(ANALYTICS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'


def _db_sql(sql, driver):
    if driver == 'postgres':
        return sql.replace('?', '%s')
    return sql


def _init_db():
    conn, driver = _db_connect()
    try:
        cur = conn.cursor()
        if driver == 'postgres':
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS request_logs (
                    id BIGSERIAL PRIMARY KEY,
                    ts BIGINT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    endpoint TEXT,
                    ip TEXT,
                    ua TEXT,
                    status INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL
                )
                '''
            )
        else:
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    endpoint TEXT,
                    ip TEXT,
                    ua TEXT,
                    status INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL
                )
                '''
            )
        cur.execute('CREATE INDEX IF NOT EXISTS idx_request_logs_ts ON request_logs(ts)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_request_logs_path ON request_logs(path)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_request_logs_ip ON request_logs(ip)')
        conn.commit()
    finally:
        conn.close()


def _get_client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _is_admin_authenticated():
    return bool(session.get('is_admin') is True)


def _verify_admin_credentials(username, password):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return False
    return hmac.compare_digest(username or '', ADMIN_USERNAME) and hmac.compare_digest(password or '', ADMIN_PASSWORD)


def _parse_time_range(args):
    now = int(time.time())
    range_key = (args.get('range') or '24h').strip().lower()
    presets = {
        '15m': 15 * 60,
        '1h': 60 * 60,
        '6h': 6 * 60 * 60,
        '24h': 24 * 60 * 60,
        '7d': 7 * 24 * 60 * 60,
        '30d': 30 * 24 * 60 * 60,
    }
    if range_key in presets:
        return now - presets[range_key], now, range_key

    from_raw = (args.get('from') or '').strip()
    to_raw = (args.get('to') or '').strip()
    if from_raw and to_raw:
        try:
            from_dt = datetime.fromisoformat(from_raw.replace('Z', '+00:00'))
            to_dt = datetime.fromisoformat(to_raw.replace('Z', '+00:00'))
            start_ts = int(from_dt.timestamp())
            end_ts = int(to_dt.timestamp())
            if end_ts > start_ts:
                return start_ts, end_ts, 'custom'
        except Exception:
            pass

    return now - presets['24h'], now, '24h'


_init_db()


@app.errorhandler(400)
def handle_bad_request(exc):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Bad request'}), 400
    return exc


@app.errorhandler(404)
def handle_not_found(exc):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return exc


@app.errorhandler(413)
def handle_payload_too_large(exc):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Payload too large'}), 413
    return exc


@app.errorhandler(Exception)
def handle_unexpected_exception(exc):
    logger.exception("Unhandled exception on %s %s", request.method, request.path)
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return 'Internal server error', 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin():
    if not _is_admin_authenticated():
        return redirect(url_for('admin_login'))
    return render_template('admin.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        if _is_admin_authenticated():
            return redirect(url_for('admin'))
        return render_template('admin_login.html')

    data = request.get_json(silent=True)
    if data:
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
    else:
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        message = 'Admin credentials are not configured on server'
        if data:
            return jsonify({'success': False, 'error': message}), 500
        return render_template('admin_login.html', error=message), 500

    if _verify_admin_credentials(username, password):
        session.clear()
        session.permanent = True
        session['is_admin'] = True
        session['admin_user'] = username
        if data:
            return jsonify({'success': True})
        return redirect(url_for('admin'))

    if data:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    return render_template('admin_login.html', error='Invalid credentials'), 401


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    if request.get_json(silent=True) is not None:
        return jsonify({'success': True})
    return redirect(url_for('admin_login'))


@app.before_request
def log_request_start():
    g.req_start = time.time()


@app.after_request
def log_request_end(response):
    try:
        if request.path.startswith('/static/'):
            return response

        duration_ms = int((time.time() - getattr(g, 'req_start', time.time())) * 1000)
        conn, driver = _db_connect()
        cur = conn.cursor()
        cur.execute(
            _db_sql(
                '''
            INSERT INTO request_logs (ts, method, path, endpoint, ip, ua, status, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
                driver,
            ),
            (
                int(time.time()),
                request.method,
                request.path,
                request.endpoint,
                _get_client_ip(),
                (request.headers.get('User-Agent') or '')[:300],
                int(response.status_code),
                duration_ms,
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    return response


def _normalize_instagram_url(url):
    try:
        parts = urlsplit(url.strip())
        if 'instagram.com' not in parts.netloc.lower():
            return url.strip()
        return urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
    except Exception:
        return url.strip()


def _normalize_tiktok_url(url):
    try:
        parts = urlsplit(url.strip())
        host = parts.netloc.lower()
        if 'tiktok.com' not in host:
            return url.strip()
        return urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
    except Exception:
        return url.strip()


def _is_image_url(url):
    lower = (url or '').lower()
    return any(lower.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp'))


def _pick_instagram_media(info, mode):
    mode = (mode or 'video').lower()
    formats = info.get('formats') or []

    video_candidates = []
    image_candidates = []

    direct_url = info.get('url')
    if direct_url:
        if _is_image_url(direct_url):
            image_candidates.append(direct_url)
        else:
            video_candidates.append(direct_url)

    for f in reversed(formats):
        u = f.get('url')
        if not u:
            continue
        vcodec = f.get('vcodec')
        acodec = f.get('acodec')
        ext = (f.get('ext') or '').lower()

        if ext in {'jpg', 'jpeg', 'png', 'webp'} or _is_image_url(u):
            image_candidates.append(u)
            continue

        if vcodec != 'none':
            video_candidates.append(u)
        elif acodec == 'none':
            image_candidates.append(u)

    thumbs = info.get('thumbnails') or []
    if thumbs:
        thumb_sorted = sorted(thumbs, key=lambda t: (t.get('width') or 0) * (t.get('height') or 0))
        largest_thumb = thumb_sorted[-1].get('url')
        if largest_thumb:
            image_candidates.append(largest_thumb)
    if info.get('thumbnail'):
        image_candidates.append(info['thumbnail'])

    image_modes = {'photo', 'dp'}
    if mode in image_modes:
        if image_candidates:
            return image_candidates[0], 'image'
        if video_candidates:
            return video_candidates[0], 'video'
        return None, None

    if video_candidates:
        return video_candidates[0], 'video'
    if image_candidates:
        return image_candidates[0], 'image'
    return None, None


def _pick_tiktok_media(info):
    formats = info.get('formats') or []
    direct_url = info.get('url')
    video_candidates = []
    image_candidates = []

    if direct_url:
        if _is_image_url(direct_url):
            image_candidates.append(direct_url)
        else:
            video_candidates.append(direct_url)

    for f in reversed(formats):
        media_url = f.get('url')
        if not media_url:
            continue
        ext = (f.get('ext') or '').lower()
        vcodec = f.get('vcodec')
        if ext in {'jpg', 'jpeg', 'png', 'webp'} or _is_image_url(media_url):
            image_candidates.append(media_url)
            continue
        if vcodec != 'none':
            video_candidates.append(media_url)

    if video_candidates:
        return video_candidates[0], 'video'
    if image_candidates:
        return image_candidates[0], 'image'
    return None, None


def _run_json_probe(url, timeout=30, use_cookies=False):
    cmd = [sys.executable, '-m', 'yt_dlp', '--dump-json', '--no-warnings', '--skip-download', '--no-playlist', url]
    if use_cookies and os.path.exists('cookies.txt'):
        cmd[3:3] = ['--cookies', 'cookies.txt']
    if 'youtube.com' in url or 'youtu.be' in url:
        yt_cookies = _youtube_cookies_path()
        if yt_cookies and '--cookies' not in cmd:
            cmd[3:3] = ['--cookies', yt_cookies]
        cmd[3:3] = ['--extractor-args', 'youtube:player_client=android,web', '--force-ipv4']

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0 or not result.stdout.strip():
        error_text = (result.stderr or result.stdout or 'yt-dlp failed').strip()
        return None, error_text

    line = result.stdout.strip().splitlines()[-1]
    return json.loads(line), None


def _cleanup_youtube_job(job_id):
    with youtube_jobs_lock:
        job = youtube_jobs.pop(job_id, None)
    if not job:
        return
    temp_dir = job.get('temp_dir')
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


def _purge_expired_youtube_jobs():
    now = time.time()
    to_delete = []
    with youtube_jobs_lock:
        for job_id, job in youtube_jobs.items():
            updated_at = job.get('updated_at', now)
            if now - updated_at > YOUTUBE_JOB_TTL_SECONDS:
                to_delete.append(job_id)
    for job_id in to_delete:
        _cleanup_youtube_job(job_id)


def _update_youtube_job(job_id, **kwargs):
    with youtube_jobs_lock:
        job = youtube_jobs.get(job_id)
        if not job:
            return
        job.update(kwargs)
        job['updated_at'] = time.time()


def _get_youtube_job_progress(job_id):
    with youtube_jobs_lock:
        job = youtube_jobs.get(job_id) or {}
        return float(job.get('progress', 0))


def _run_youtube_download_with_progress(job_id, url, quality, output_template):
    if quality == '360p':
        format_options = [
            '18/best[ext=mp4][height<=360][acodec!=none][vcodec!=none]/best[height<=360]/best',
            'best[height<=360][acodec!=none][vcodec!=none]/best[height<=360]/best',
        ]
    else:
        format_options = [
            '22/best[ext=mp4][height<=720][acodec!=none][vcodec!=none]/best[height<=720]/best',
            'best[height<=720][acodec!=none][vcodec!=none]/best[height<=720]/best',
        ]

    last_error = 'Download failed'
    percent_re = re.compile(r'(\d+(?:\.\d+)?)%')

    for format_str in format_options:
        yt_cookies = _youtube_cookies_path()
        cmd = [
            sys.executable,
            '-m',
            'yt_dlp',
            '-f', format_str,
            '-o', output_template,
            '--newline',
            '--no-warnings',
            '--no-playlist',
            '--no-check-certificates',
            '--force-ipv4',
            '--extractor-args', 'youtube:player_client=android,web',
            '--concurrent-fragments', '4',
            url,
        ]
        if yt_cookies:
            cmd[3:3] = ['--cookies', yt_cookies]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output_lines = []

        for line in process.stdout:
            text_line = line.strip()
            if not text_line:
                continue
            output_lines.append(text_line)

            if '[download]' in text_line:
                percent_match = percent_re.search(text_line)
                if percent_match:
                    progress = float(percent_match.group(1))
                    _update_youtube_job(
                        job_id,
                        status='downloading',
                        message=f'Downloading {quality}... {progress:.1f}%',
                        progress=progress,
                    )
                elif 'Destination' in text_line:
                    _update_youtube_job(
                        job_id,
                        status='downloading',
                        message=f'Preparing {quality} file...',
                        progress=max(5, _get_youtube_job_progress(job_id)),
                    )

        process.wait(timeout=20)
        if process.returncode == 0:
            return True, ''

        last_error = '\n'.join(output_lines[-5:]) if output_lines else 'Download failed'
        _update_youtube_job(
            job_id,
            status='downloading',
            message='Retrying with fallback format...',
            progress=min(95, _get_youtube_job_progress(job_id) + 5),
        )

    return False, last_error


def _youtube_download_worker(job_id, url, quality):
    temp_dir = tempfile.mkdtemp(prefix='yt_bg_')
    output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')
    _update_youtube_job(
        job_id,
        status='downloading',
        message=f'Starting {quality} download...',
        progress=2,
        temp_dir=temp_dir,
    )

    try:
        ok, err = _run_youtube_download_with_progress(job_id, url, quality, output_template)
        if not ok:
            _update_youtube_job(job_id, status='error', error=f'Failed to download {quality}: {err[:250]}')
            return

        files = [
            os.path.join(temp_dir, name)
            for name in os.listdir(temp_dir)
            if os.path.isfile(os.path.join(temp_dir, name))
        ]
        if not files:
            _update_youtube_job(job_id, status='error', error='Download failed - no output file found')
            return

        temp_file = max(files, key=os.path.getsize)
        file_size = os.path.getsize(temp_file)
        if file_size < 1024:
            _update_youtube_job(job_id, status='error', error='Download failed - output file is too small')
            return

        _update_youtube_job(
            job_id,
            status='ready',
            progress=100,
            message='Download ready',
            file_path=temp_file,
            file_size=file_size,
            download_name=f'youtube-{quality}.mp4',
        )
    except Exception as exc:
        _update_youtube_job(job_id, status='error', error=str(exc))


@app.route('/api/download/instagram', methods=['POST'])
def download_instagram():
    try:
        data = request.get_json(silent=True) or {}
        url = _normalize_instagram_url((data.get('url') or '').strip())
        mode = (data.get('mode') or 'video').strip().lower()
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        info = None
        last_error = ''

        # Try cookie-auth first (if available), then fallback without cookies.
        for use_cookies in (True, False):
            if use_cookies and not os.path.exists('cookies.txt'):
                continue
            info, probe_error = _run_json_probe(url, timeout=35, use_cookies=use_cookies)
            if info:
                break
            last_error = probe_error or last_error

        if not info:
            message = 'Failed to process Instagram URL'
            if last_error:
                message = f'{message}: {last_error[:220]}'
            return jsonify({'success': False, 'error': message}), 400

        media_url, media_type = _pick_instagram_media(info, mode)

        if not media_url:
            return jsonify({'success': False, 'error': 'No downloadable media found'}), 400

        thumbnail_url = info.get('thumbnail', '')
        proxied_thumbnail = ''
        if thumbnail_url:
            proxied_thumbnail = '/api/thumbnail?url=' + requests.utils.quote(thumbnail_url, safe='')

        return jsonify({
            'success': True,
            'videoUrl': media_url,  # Backward compatibility with existing frontend key.
            'mediaUrl': media_url,
            'mediaType': media_type or 'video',
            'mode': mode,
            'thumbnail': proxied_thumbnail,
            'username': info.get('uploader', 'Instagram User')
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Instagram request timed out'}), 408
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/download/tiktok', methods=['POST'])
def download_tiktok():
    try:
        data = request.get_json(silent=True) or {}
        url = _normalize_tiktok_url((data.get('url') or '').strip())
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        info, probe_error = _run_json_probe(url, timeout=35, use_cookies=False)
        if not info:
            message = 'Failed to process TikTok URL'
            if probe_error:
                message = f'{message}: {probe_error[:220]}'
            return jsonify({'success': False, 'error': message}), 400

        media_url, media_type = _pick_tiktok_media(info)
        if not media_url:
            return jsonify({'success': False, 'error': 'No downloadable media found'}), 400

        thumbnail_url = info.get('thumbnail', '')
        proxied_thumbnail = ''
        if thumbnail_url:
            proxied_thumbnail = '/api/thumbnail?url=' + requests.utils.quote(thumbnail_url, safe='')

        return jsonify({
            'success': True,
            'mediaUrl': media_url,
            'mediaType': media_type or 'video',
            'thumbnail': proxied_thumbnail,
            'username': info.get('uploader', 'TikTok User'),
            'title': info.get('title', 'TikTok Video')
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'TikTok request timed out'}), 408
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/youtube/info', methods=['POST'])
def youtube_info():
    try:
        data = request.get_json(silent=True) or {}
        url = (data.get('url') or '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        info, probe_error = _run_json_probe(url, timeout=25)
        if not info:
            message = 'Failed to process YouTube URL'
            if probe_error:
                message = f'{message}: {probe_error[:220]}'
            if probe_error and "Sign in to confirm you're not a bot" in probe_error:
                message += ' | Server admin must configure YTDLP_COOKIES_B64 or YTDLP_COOKIES_TXT.'
            return jsonify({'success': False, 'error': message}), 400

        return jsonify({
            'success': True,
            'thumbnail': info.get('thumbnail', ''),
            'title': info.get('title', 'YouTube Video')
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'YouTube info request timed out'}), 408
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/youtube/download/start', methods=['POST'])
def youtube_download_start():
    _purge_expired_youtube_jobs()
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    quality = (data.get('quality') or '720p').strip().lower()
    if quality not in {'360p', '720p'}:
        quality = '720p'
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400

    job_id = uuid.uuid4().hex
    now = time.time()
    with youtube_jobs_lock:
        if len(youtube_jobs) >= MAX_QUEUED_JOBS:
            return jsonify({'success': False, 'error': 'Server is busy. Try again in a moment.'}), 429
        youtube_jobs[job_id] = {
            'job_id': job_id,
            'status': 'queued',
            'message': 'Queued...',
            'progress': 0,
            'quality': quality,
            'url': url,
            'created_at': now,
            'updated_at': now,
        }

    youtube_executor.submit(_youtube_download_worker, job_id, url, quality)

    return jsonify({'success': True, 'jobId': job_id})


@app.route('/api/youtube/download/status/<job_id>')
def youtube_download_status(job_id):
    _purge_expired_youtube_jobs()
    with youtube_jobs_lock:
        job = youtube_jobs.get(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found or expired'}), 404

        payload = {
            'success': True,
            'jobId': job_id,
            'status': job.get('status', 'queued'),
            'message': job.get('message', ''),
            'progress': float(job.get('progress', 0)),
        }
        if job.get('error'):
            payload['error'] = job['error']
        if job.get('status') == 'ready':
            payload['downloadUrl'] = f'/api/youtube/download/file/{job_id}'
            payload['fileSizeMB'] = round((job.get('file_size', 0) / (1024 * 1024)), 2)

    return jsonify(payload)


@app.route('/api/youtube/download/file/<job_id>')
def youtube_download_file(job_id):
    with youtube_jobs_lock:
        job = youtube_jobs.get(job_id)
        if not job:
            return 'Job not found or expired', 404
        if job.get('status') != 'ready':
            return 'File is not ready yet', 409
        file_path = job.get('file_path')
        download_name = job.get('download_name') or 'youtube-video.mp4'
        temp_dir = job.get('temp_dir')
        if not file_path or not os.path.exists(file_path):
            return 'Downloaded file no longer exists', 404

    response = send_file(
        file_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='video/mp4'
    )

    @response.call_on_close
    def cleanup():
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        finally:
            with youtube_jobs_lock:
                youtube_jobs.pop(job_id, None)

    return response


@app.route('/api/youtube/download')
def youtube_download():
    temp_dir = None

    try:
        url = (request.args.get('url') or '').strip()
        quality = (request.args.get('quality') or '720p').strip().lower()
        if quality not in {'360p', '720p'}:
            quality = '720p'

        if not url:
            return 'No URL provided', 400

        temp_dir = tempfile.mkdtemp(prefix='yt_')
        output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')

        # Retry strategies to reduce YouTube 403 issues.
        if quality == '360p':
            format_options = [
                '18/best[ext=mp4][height<=360][acodec!=none][vcodec!=none]/best[height<=360]/best',
                'best[height<=360][acodec!=none][vcodec!=none]/best[height<=360]/best',
            ]
        else:
            format_options = [
                '22/best[ext=mp4][height<=720][acodec!=none][vcodec!=none]/best[height<=720]/best',
                'best[height<=720][acodec!=none][vcodec!=none]/best[height<=720]/best',
            ]

        last_error = ''
        for format_str in format_options:
            yt_cookies = _youtube_cookies_path()
            cmd = [
                sys.executable,
                '-m',
                'yt_dlp',
                '-f', format_str,
                '-o', output_template,
                '--no-warnings',
                '--no-playlist',
                '--no-check-certificates',
                '--force-ipv4',
                '--extractor-args', 'youtube:player_client=android,web',
                '--concurrent-fragments', '4',
                url,
            ]
            if yt_cookies:
                cmd[3:3] = ['--cookies', yt_cookies]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DOWNLOAD_TIMEOUT_SECONDS)
            if result.returncode == 0:
                break
            last_error = (result.stderr or result.stdout or 'Download failed').strip()
        else:
            return f'Failed to download {quality}: {last_error[:250]}', 400

        files = [
            os.path.join(temp_dir, name)
            for name in os.listdir(temp_dir)
            if os.path.isfile(os.path.join(temp_dir, name))
        ]
        if not files:
            return 'Download failed - no output file found', 404

        temp_file = max(files, key=os.path.getsize)
        if os.path.getsize(temp_file) < 1024:
            return 'Download failed - output file is too small', 400

        response = send_file(
            temp_file,
            as_attachment=True,
            download_name=f'youtube-{quality}.mp4',
            mimetype='video/mp4'
        )

        @response.call_on_close
        def cleanup():
            try:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

        return response

    except subprocess.TimeoutExpired:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        return 'Download timed out', 408
    except Exception as exc:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        return str(exc), 500


@app.route('/api/download/instagram/file')
@app.route('/api/download/tiktok/file')
def download_instagram_file():
    media_url = (request.args.get('media_url') or request.args.get('video_url') or '').strip()
    media_type = (request.args.get('media_type') or 'video').strip().lower()
    if not media_url:
        return 'No media URL provided', 400

    parsed = urlsplit(media_url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return 'Invalid media URL', 400

    try:
        upstream = requests.get(media_url, stream=True, timeout=30)
        if upstream.status_code != 200:
            return 'Failed to fetch Instagram media file', 400

        def generate():
            for chunk in upstream.iter_content(chunk_size=1024 * 64):
                if chunk:
                    yield chunk

        filename = 'instagram-media.mp4'
        if media_type == 'image':
            filename = 'instagram-image.jpg'

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Cache-Control': 'no-store',
        }
        default_type = 'image/jpeg' if media_type == 'image' else 'video/mp4'
        content_type = upstream.headers.get('Content-Type') or default_type
        content_length = upstream.headers.get('Content-Length')
        if content_length:
            headers['Content-Length'] = content_length

        return Response(
            stream_with_context(generate()),
            headers=headers,
            content_type=content_type
        )
    except Exception:
        return 'Error downloading Instagram video', 500


@app.route('/api/admin/stats')
def admin_stats():
    if not _is_admin_authenticated():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    start_ts, end_ts, selected_range = _parse_time_range(request.args)
    if end_ts <= start_ts:
        return jsonify({'success': False, 'error': 'Invalid time range'}), 400

    base_where = '''
        WHERE ts >= ? AND ts <= ?
          AND path NOT LIKE '/api/admin/%'
          AND path <> '/admin'
    '''
    params = (start_ts, end_ts)
    conn, driver = _db_connect()
    cur = conn.cursor()
    try:
        cur.execute(_db_sql(f'SELECT COUNT(*) FROM request_logs {base_where}', driver), params)
        total_hits = cur.fetchone()[0]

        cur.execute(_db_sql(f'SELECT COUNT(DISTINCT ip) FROM request_logs {base_where}', driver), params)
        unique_visitors = cur.fetchone()[0]

        cur.execute(
            _db_sql(
                f'''
            SELECT path, COUNT(*) AS count
            FROM request_logs
            {base_where}
            GROUP BY path
            ORDER BY count DESC
            LIMIT 10
            ''',
                driver,
            ),
            params,
        )
        top_paths = [{'path': row[0], 'count': row[1]} for row in cur.fetchall()]

        cur.execute(
            _db_sql(
                f'''
            SELECT
              SUM(CASE WHEN path = '/' THEN 1 ELSE 0 END) AS home_hits,
              SUM(CASE WHEN path LIKE '/api/download/instagram%' THEN 1 ELSE 0 END) AS instagram_hits,
              SUM(CASE WHEN path LIKE '/api/youtube%' THEN 1 ELSE 0 END) AS youtube_hits,
              SUM(CASE WHEN path LIKE '/api/download/tiktok%' THEN 1 ELSE 0 END) AS tiktok_hits
            FROM request_logs
            {base_where}
            ''',
                driver,
            ),
            params,
        )
        row = cur.fetchone()
        platform_breakdown = {
            'home': int(row[0] or 0),
            'instagram': int(row[1] or 0),
            'youtube': int(row[2] or 0),
            'tiktok': int(row[3] or 0),
        }

        cur.execute(
            _db_sql(
                f'''
            SELECT ts, ip, method, path, status, latency_ms
            FROM request_logs
            {base_where}
            ORDER BY id DESC
            LIMIT 40
            ''',
                driver,
            ),
            params,
        )
        recent_activity = [
            {
                'ts': row[0],
                'ip': row[1],
                'method': row[2],
                'path': row[3],
                'status': row[4],
                'latencyMs': row[5],
            }
            for row in cur.fetchall()
        ]

        span = end_ts - start_ts
        bucket = 300 if span <= 2 * 3600 else (3600 if span <= 10 * 24 * 3600 else 86400)
        if driver == 'postgres':
            cur.execute(
                '''
                SELECT (FLOOR(ts::numeric / %s) * %s)::bigint AS bucket_ts, COUNT(*) AS count
                FROM request_logs
                WHERE ts >= %s AND ts <= %s
                  AND path NOT LIKE '/api/admin/%'
                  AND path <> '/admin'
                GROUP BY bucket_ts
                ORDER BY bucket_ts ASC
                ''',
                (bucket, bucket, start_ts, end_ts),
            )
        else:
            cur.execute(
                '''
                SELECT ((ts / ?) * ?) AS bucket_ts, COUNT(*) AS count
                FROM request_logs
                WHERE ts >= ? AND ts <= ?
                  AND path NOT LIKE '/api/admin/%'
                  AND path <> '/admin'
                GROUP BY bucket_ts
                ORDER BY bucket_ts ASC
                ''',
                (bucket, bucket, start_ts, end_ts),
            )
        time_series = [{'ts': row[0], 'count': row[1]} for row in cur.fetchall()]

        return jsonify(
            {
                'success': True,
                'range': selected_range,
                'startTs': start_ts,
                'endTs': end_ts,
                'summary': {
                    'totalHits': total_hits,
                    'uniqueVisitors': unique_visitors,
                    'avgLatencyMs': (
                        round(
                            (
                                sum(item['latencyMs'] for item in recent_activity)
                                / len(recent_activity)
                            ),
                            1,
                        )
                        if recent_activity
                        else 0
                    ),
                },
                'platformBreakdown': platform_breakdown,
                'topPaths': top_paths,
                'timeSeries': time_series,
                'recentActivity': recent_activity,
            }
        )
    finally:
        conn.close()


@app.route('/api/admin/me')
def admin_me():
    if not _is_admin_authenticated():
        return jsonify({'success': False, 'authenticated': False}), 401
    return jsonify({'success': True, 'authenticated': True, 'username': session.get('admin_user', 'admin')})


@app.route('/api/thumbnail')
def get_thumbnail():
    thumbnail_url = request.args.get('url')
    if not thumbnail_url:
        return 'No URL provided', 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.instagram.com/',
        }
        response = requests.get(thumbnail_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return send_file(BytesIO(response.content), mimetype='image/jpeg')
        return 'Failed to fetch thumbnail', 404
    except Exception:
        return 'Error fetching thumbnail', 500


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/ready')
def ready():
    with youtube_jobs_lock:
        pending_jobs = len(youtube_jobs)
    return jsonify(
        {
            'status': 'ready',
            'maxWorkers': MAX_DOWNLOAD_WORKERS,
            'pendingJobs': pending_jobs,
            'maxQueuedJobs': MAX_QUEUED_JOBS,
            'time': int(time.time()),
        }
    )


if __name__ == '__main__':
    _init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
