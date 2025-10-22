from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import json
import os
import requests
from io import BytesIO

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        print(f"\n{'='*60}")
        print(f"Processing: {url}")
        print(f"{'='*60}")

        # Check if cookies.txt exists
        cookies_file = 'cookies.txt'

        if os.path.exists(cookies_file):
            print(f"Using cookies from {cookies_file}")
            cmd = [
                'yt-dlp',
                '--cookies', cookies_file,
                '--dump-json',
                '--no-warnings',
                '--skip-download',
                url
            ]
        else:
            print("No cookies.txt found, trying without cookies...")
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                '--skip-download',
                url
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            error = result.stderr
            print(f"Error: {error}")

            if 'private' in error.lower():
                return jsonify({'success': False, 'error': 'This account is private'}), 400
            elif 'not found' in error.lower():
                return jsonify({'success': False, 'error': 'Post not found'}), 400
            elif 'rate-limit' in error.lower() or 'login required' in error.lower():
                if not os.path.exists(cookies_file):
                    return jsonify({
                        'success': False, 
                        'error': 'Instagram rate limit. Please export cookies (see instructions in terminal)'
                    }), 400
                else:
                    return jsonify({'success': False, 'error': 'Rate limited. Try again in a few minutes'}), 400
            else:
                return jsonify({'success': False, 'error': 'Failed to process URL'}), 400

        # Parse JSON
        info = json.loads(result.stdout)

        # Get video URL
        video_url = info.get('url') or (info.get('formats', [{}])[-1].get('url'))

        if not video_url:
            return jsonify({'success': False, 'error': 'No video found'}), 400

        # Get thumbnail
        thumbnail_url = info.get('thumbnail', '')
        proxied_thumbnail = ''
        if thumbnail_url:
            proxied_thumbnail = '/api/thumbnail?url=' + requests.utils.quote(thumbnail_url)

        print("✅ Success!")

        return jsonify({
            'success': True,
            'videoUrl': video_url,
            'thumbnail': proxied_thumbnail,
            'username': info.get('uploader', 'Instagram User'),
            'quality': 'HD'
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Request timeout'}), 400
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid response'}), 400
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/thumbnail')
def get_thumbnail():
    """Proxy thumbnail to bypass CORS"""
    thumbnail_url = request.args.get('url')
    if not thumbnail_url:
        return "No URL", 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.instagram.com/',
        }
        response = requests.get(thumbnail_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return send_file(BytesIO(response.content), mimetype='image/jpeg')
        return "Failed", 404
    except Exception as e:
        return "Error", 500

@app.route('/api/health')
def health():
    cookies_status = "✅ Found" if os.path.exists('cookies.txt') else "❌ Not found"
    return jsonify({'status': 'ok', 'cookies': cookies_status})

if __name__ == '__main__':
    print("="*70)
    print("🚀 Instagram Downloader")
    print("="*70)

    if not os.path.exists('cookies.txt'):
        print("⚠️  WARNING: cookies.txt not found!")
        print()
        print("📋 SETUP INSTRUCTIONS:")
        print()
        print("Method 1: Use Chrome Extension (EASIEST)")
        print("   1. Install: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
        print("   2. Go to instagram.com (login if needed)")
        print("   3. Click extension icon → 'Export' → Save as cookies.txt")
        print("   4. Move cookies.txt to this folder: D:\\Instagram_video_downloader\\")
        print()
        print("Method 2: Use yt-dlp command")
        print("   Run: yt-dlp --cookies-from-browser chrome:cookies.txt")
        print()
        print("Method 3: Try without cookies (may work for public accounts)")
        print("   Just start the app and try - works sometimes!")
        print()
    else:
        print("✅ cookies.txt found!")
        print()

    print("📍 Visit: http://localhost:5000")
    print("="*70)

    app.run(debug=True, host='0.0.0.0', port=5000)
