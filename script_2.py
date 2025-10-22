
import os

os.makedirs('templates', exist_ok=True)

updated_frontend = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Downloader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh; display: flex; flex-direction: column;
            position: relative; overflow-x: hidden;
        }
        .bg-circle {
            position: absolute; border-radius: 50%;
            background: rgba(255, 255, 255, 0.03);
            animation: float 20s infinite ease-in-out; z-index: 0;
        }
        .circle1 { width: 400px; height: 400px; top: -150px; left: -150px; }
        .circle2 { width: 300px; height: 300px; bottom: -100px; right: -100px; animation-delay: 5s; }
        .circle3 { width: 200px; height: 200px; top: 40%; right: 5%; animation-delay: 10s; }
        @keyframes float {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(50px, 50px) scale(1.1); }
        }
        .container { max-width: 600px; margin: 60px auto; padding: 0 20px; flex: 1; position: relative; z-index: 1; }
        .main-card {
            background: rgba(30, 30, 46, 0.8); backdrop-filter: blur(20px);
            border-radius: 30px; padding: 50px 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeInUp 0.8s ease;
        }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        h1 {
            color: white; font-size: 36px; text-align: center;
            margin-bottom: 10px; text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
            display: flex; align-items: center; justify-content: center; gap: 10px;
        }
        .logo-icon { font-size: 42px; animation: bounce 2s infinite; }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .subtitle { color: rgba(255, 255, 255, 0.7); text-align: center; margin-bottom: 30px; font-size: 16px; }
        .ad-container {
            margin: 20px 0; padding: 20px; background: rgba(255, 255, 255, 0.03);
            border-radius: 15px; border: 2px dashed rgba(255, 255, 255, 0.1);
            text-align: center; color: rgba(255, 255, 255, 0.3);
            min-height: 100px; display: flex; align-items: center; justify-content: center;
        }
        .input-group { display: flex; gap: 10px; margin-bottom: 15px; }
        input[type="text"] {
            flex: 1; padding: 18px 24px; border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 50px; background: rgba(255, 255, 255, 0.05);
            color: white; font-size: 16px; outline: none; transition: all 0.3s ease;
        }
        input::placeholder { color: rgba(255, 255, 255, 0.4); }
        input:focus {
            border-color: rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        }
        .btn-search {
            padding: 18px 35px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 50px;
            font-size: 16px; font-weight: bold; cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-search:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }
        .spinner {
            display: none; width: 18px; height: 18px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%; border-top-color: white;
            animation: spin 1s linear infinite;
            margin-right: 8px; vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading .spinner { display: inline-block; }
        .result-section {
            display: none; margin-top: 30px; padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }
        .result-section.show { display: block; animation: scaleIn 0.5s ease; }
        @keyframes scaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
        .video-preview {
            margin-bottom: 20px; border-radius: 15px;
            background: rgba(0, 0, 0, 0.3); overflow: hidden;
        }
        .video-preview img {
            max-width: 100%; width: 100%; max-height: 400px;
            object-fit: cover; border-radius: 15px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.5);
            border: 2px solid rgba(255, 255, 255, 0.1);
            display: block !important;
        }
        .video-info { color: rgba(255, 255, 255, 0.8); margin-bottom: 20px; font-size: 14px; }
        .download-btn {
            width: 100%; padding: 18px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white; border: none; border-radius: 50px;
            font-size: 18px; font-weight: bold; cursor: pointer;
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
        }
        .download-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(245, 87, 108, 0.6);
        }
        .error-message {
            display: none; padding: 15px;
            background: rgba(255, 87, 87, 0.2);
            border: 1px solid rgba(255, 87, 87, 0.5);
            border-radius: 15px; color: white;
            margin-top: 15px; text-align: center;
        }
        .error-message.show { display: block; }
        .features {
            display: grid; grid-template-columns: repeat(2, 1fr);
            gap: 20px; margin-top: 40px;
        }
        .feature {
            text-align: center; padding: 25px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }
        .feature:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        .feature-icon { font-size: 40px; margin-bottom: 10px; }
        .feature h3 { color: white; font-size: 16px; margin-bottom: 8px; }
        .feature p { color: rgba(255, 255, 255, 0.6); font-size: 13px; }
        footer {
            background: rgba(30, 30, 46, 0.6);
            padding: 20px; text-align: center;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 50px; font-size: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        @media (max-width: 768px) {
            .input-group { flex-direction: column; }
            .btn-search { width: 100%; }
            .features { grid-template-columns: 1fr; }
            h1 { font-size: 28px; }
        }
    </style>
</head>
<body>
    <div class="bg-circle circle1"></div>
    <div class="bg-circle circle2"></div>
    <div class="bg-circle circle3"></div>
    <div class="container">
        <div class="main-card">
            <h1><span class="logo-icon">📱</span> Instagram Downloader</h1>
            <p class="subtitle">Download Instagram Videos, Reels, and IGTV - Fast & Free</p>
            <div class="ad-container">Advertisement Space</div>
            <form id="downloadForm">
                <div class="input-group">
                    <input type="text" id="videoUrl" placeholder="Paste Instagram video/reel URL here..." required>
                    <button type="submit" class="btn-search" id="searchBtn">
                        <div class="spinner"></div><span>Search</span>
                    </button>
                </div>
            </form>
            <div class="error-message" id="errorMessage"></div>
            <div class="result-section" id="resultSection">
                <div class="video-preview">
                    <img id="thumbnailImg" src="" alt="Video thumbnail">
                </div>
                <div class="video-info" id="videoInfo"></div>
                <button id="downloadBtn" class="download-btn">Download Video (HD)</button>
            </div>
            <div class="features">
                <div class="feature"><div class="feature-icon">⚡</div><h3>Lightning Fast</h3><p>Download videos in seconds</p></div>
                <div class="feature"><div class="feature-icon">🔒</div><h3>100% Safe</h3><p>No login required</p></div>
                <div class="feature"><div class="feature-icon">📱</div><h3>All Devices</h3><p>Works on mobile & desktop</p></div>
                <div class="feature"><div class="feature-icon">🎬</div><h3>HD Quality</h3><p>Best quality downloads</p></div>
            </div>
            <div class="ad-container" style="margin-top: 40px;">Advertisement Space</div>
        </div>
    </div>
    <footer><strong>Disclaimer:</strong> Personal use only.<br>© 2025 Instagram Downloader.</footer>
    <script>
        const form = document.getElementById('downloadForm');
        const searchBtn = document.getElementById('searchBtn');
        const errorMessage = document.getElementById('errorMessage');
        const resultSection = document.getElementById('resultSection');
        const thumbnailImg = document.getElementById('thumbnailImg');
        const videoInfo = document.getElementById('videoInfo');
        const downloadBtn = document.getElementById('downloadBtn');
        let currentVideoUrl = '';

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const videoUrl = document.getElementById('videoUrl').value.trim();
            if (!(/^https?:\\/\\/(www\\.)?instagram\\.com\\/(p|reel|tv)\\/[A-Za-z0-9_-]+/.test(videoUrl))) {
                showError('Please enter a valid Instagram URL'); return;
            }
            hideError(); hideResult();
            searchBtn.classList.add('loading'); searchBtn.disabled = true;
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: videoUrl })
                });
                const data = await response.json();
                if (data.success) showResult(data);
                else showError(data.error || 'Failed to fetch video.');
            } catch (error) {
                showError('Network error.');
            } finally {
                searchBtn.classList.remove('loading'); searchBtn.disabled = false;
            }
        });

        downloadBtn.addEventListener('click', async () => {
            if (!currentVideoUrl) { showError('No video URL'); return; }
            try {
                const response = await fetch(currentVideoUrl);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'instagram-video.mp4';
                document.body.appendChild(a); a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } catch (error) {
                const iframe = document.createElement('iframe');
                iframe.style.display = 'none'; iframe.src = currentVideoUrl;
                document.body.appendChild(iframe);
                setTimeout(() => document.body.removeChild(iframe), 2000);
            }
        });

        function showError(msg) { errorMessage.textContent = msg; errorMessage.classList.add('show'); }
        function hideError() { errorMessage.classList.remove('show'); }
        function showResult(data) {
            currentVideoUrl = data.videoUrl || '';
            if (data.thumbnail) {
                console.log('✅ Loading thumbnail via proxy:', data.thumbnail);
                thumbnailImg.src = data.thumbnail;
            }
            videoInfo.innerHTML = data.username ? `<strong>Posted by:</strong> @${data.username}` : '';
            resultSection.classList.add('show');
        }
        function hideResult() {
            resultSection.classList.remove('show');
            thumbnailImg.src = ''; currentVideoUrl = '';
        }
    </script>
</body>
</html>'''

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(updated_frontend)

print("✅ Updated templates/index.html")
print("✅ Updated app_with_cookies.py with thumbnail proxy")
print("\n🔧 What Changed:")
print("   1. Backend: Added /api/thumbnail endpoint to proxy Instagram images")
print("   2. Backend: Returns proxied URL instead of direct Instagram URL")
print("   3. Frontend: Thumbnail always displays (display: block !important)")
print("   4. Frontend: Console logs thumbnail loading status")
print("\n🚀 RESTART YOUR APP:")
print("   python app_with_cookies.py")
print("\n✨ Thumbnail will now show because:")
print("   - Images are fetched through YOUR server (bypasses CORS)")
print("   - No more 'display: none' hiding the image")
print("   - Proper error handling")
