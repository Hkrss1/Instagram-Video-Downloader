# 📱 Instagram-Video-Downloader : https://instagram-video-downloader-rdgz.onrender.com

> Download Instagram videos, reels, and IGTV with a beautiful dark theme UI

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-personal%20use-orange.svg)
![Status](https://img.shields.io/badge/status-working-brightgreen.svg)

A sleek, modern web application for downloading Instagram videos with a beautiful dark greyish-black theme, smooth animations, and intuitive user interface.

## ✨ Features

- 🎨 **Beautiful Dark Theme** - Greyish-black gradient (#1a1a2e → #16213e → #0f3460)
- 🖼️ **Thumbnail Preview** - See video thumbnail before downloading
- ⚡ **Lightning Fast** - Download videos in seconds
- 📱 **Mobile Responsive** - Works perfectly on all devices
- 🎭 **Smooth Animations** - Floating circles, bouncing icons, and transitions
- 💾 **Direct Download** - No preview tab, downloads directly to your device
- 🔒 **Safe & Secure** - No login required for public accounts
- 🎬 **HD Quality** - Best quality video downloads
- 👤 **Username Display** - Shows the content creator's username

## 🎥 Demo

The application features:
- Animated floating background circles
- Glassmorphism card effects
- Smooth fade-in and scale animations
- Hover effects on all interactive elements
- Real-time error handling with shake animations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Chrome browser (for cookie export)
- Instagram account (for authentication)

### Installation

1. **Clone or download the project**
cd D:\Instagram_video_downloader

text

2. **Create virtual environment (recommended)**
python -m venv venv
venv\Scripts\activate # Windows

text

3. **Install dependencies**
pip install -r requirements.txt

text

### Setup Instagram Cookies

**Important:** Due to Instagram's rate limiting, you need to export your cookies.

#### Method 1: Chrome Extension (Recommended)

1. Install [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Go to [instagram.com](https://www.instagram.com) and login
3. Click the extension icon
4. Click "Export" → Save as `cookies.txt`
5. Move `cookies.txt` to project folder: `D:\Instagram_video_downloader\`

#### Method 2: Use Firefox

Firefox doesn't have DPAPI encryption issues. Just login to Instagram in Firefox and the app will automatically use Firefox cookies.

For detailed instructions, see [DPAPI_FIX_GUIDE.md](DPAPI_FIX_GUIDE.md)

### Run the Application

python app_with_cookies.py

text

Open your browser and visit: [**http://localhost:5000**](http://localhost:5000)

## 📖 Usage

1. **Paste Instagram URL** - Copy any Instagram video/reel URL
2. **Click Search** - Wait 5-10 seconds for processing
3. **Preview Thumbnail** - See the video preview
4. **Download** - Click "Download Video (HD)" button
5. **Enjoy!** - Video downloads directly to your device

### Supported URL Formats

✅ https://www.instagram.com/reel/ABC123/
✅ https://www.instagram.com/p/ABC123/
✅ https://www.instagram.com/tv/ABC123/

text

## 🛠️ Technologies

| Component | Technology |
|-----------|------------|
| **Backend** | Flask (Python) |
| **Video Extraction** | yt-dlp |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Design** | Dark theme with animations |
| **Image Proxy** | Flask endpoint (CORS bypass) |
| **Authentication** | Cookie-based (Netscape format) |

## 📁 Project Structure

Instagram_video_downloader/
│
├── templates/
│ └── index.html # Frontend UI with dark theme
│
├── app_with_cookies.py # Main Flask application
├── cookies.txt # Instagram cookies (not in git)
├── requirements.txt # Python dependencies
├── README.md # This file
├── DPAPI_FIX_GUIDE.md # Cookie export guide
└── .gitignore # Git ignore rules

text

## 🎨 UI Features

### Color Scheme
- **Background Gradient:** `#1a1a2e` → `#16213e` → `#0f3460`
- **Card Background:** `rgba(30, 30, 46, 0.8)` with backdrop blur
- **Accent Colors:** Purple gradient `#667eea` → `#764ba2`
- **Download Button:** Pink gradient `#f093fb` → `#f5576c`

### Animations
- Floating background circles (20s loop)
- Bouncing logo icon (2s loop)
- Fade-in effects on page load
- Scale-in animation for results
- Hover lift effects on feature cards
- Smooth transitions everywhere

## 🔧 Configuration

No configuration needed! The app works out of the box once cookies are exported.

### Optional: Environment Variables

You can optionally use environment variables:

.env file
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

text

## 🐛 Troubleshooting

### "Failed to process URL"
**Solution:** Make sure `cookies.txt` is in the project folder and properly exported.

### "Rate limit reached"
**Solution:** 
- Wait 15-30 minutes
- Export fresh cookies
- Try using a different network/IP

### "Private account"
**Solution:** Only public Instagram accounts work. Make sure you're logged into Instagram when exporting cookies if you need to access content from accounts you follow.

### "Thumbnail not showing"
**Solution:** The thumbnail is proxied through the backend to bypass CORS. Check browser console (F12) for errors. Make sure the Flask server is running.

### DPAPI Decryption Error (Windows)
**Solution:** This is why we use `cookies.txt` file instead of reading browser cookies directly. Follow the cookie export instructions above.

## 📊 Dependencies

Flask==3.0.0 # Web framework
flask-cors==4.0.0 # CORS handling
requests==2.31.0 # HTTP library
yt-dlp # Video extraction

text

## ⚠️ Important Notes

- **Personal Use Only** - This tool is for personal use
- **Respect Copyright** - Only download content you have permission to use
- **Public Accounts** - Works best with public Instagram accounts
- **Rate Limits** - Instagram has rate limits; don't abuse the service
- **Cookies Expire** - Re-export cookies every 30 days or if you encounter issues

## 🔐 Security & Privacy

- Cookies are stored locally and never sent anywhere except Instagram
- No data is logged or stored by the application
- All processing happens on your local machine
- Uses HTTPS for all Instagram connections

## 📝 License

This project is for **personal use only**. Please respect copyright laws and obtain permission from content creators before downloading their content.

## 🤝 Contributing

This is a personal project. Feel free to fork and modify for your own use.

## 💡 Tips

- Keep your Instagram session active in the browser
- Export fresh cookies if you encounter rate limits
- Use public account URLs for best results
- The app works without cookies sometimes, but success rate is lower
- Refresh cookies every 30 days or when they expire

## 🎯 Roadmap

- [x] Dark theme UI
- [x] Thumbnail preview
- [x] Direct download functionality
- [x] Cookie authentication
- [x] Mobile responsive design
- [x] Thumbnail CORS bypass
- [ ] Batch download multiple videos
- [ ] Download history/queue
- [ ] Quality selection (HD/SD)
- [ ] Dark/Light theme toggle
- [ ] Download progress indicator

## 📞 Support : ankit50102002@gmail.com

For issues related to:
- **Cookie export:** See [DPAPI_FIX_GUIDE.md](DPAPI_FIX_GUIDE.md)
- **Project structure:** See [FINAL_PROJECT_STRUCTURE.md](FINAL_PROJECT_STRUCTURE.md)
- **yt-dlp issues:** Visit [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video extraction
- [Instagram](https://www.instagram.com/) - Content platform

## 📅 Version History

- **v1.0.0** (October 2025) - Initial release
  - Dark theme UI
  - Cookie-based authentication
  - Thumbnail proxy
  - Direct download

---

**Made with ❤️ for personal use**

*Enjoy downloading Instagram videos with style!* 🚀
Save this as README.md in your project root folder. This comprehensive README includes:

✅ Project description and badges
✅ Complete feature list
✅ Detailed setup instructions (especially cookies)
✅ Usage guide with examples
✅ Technology stack
✅ Project structure
✅ UI/UX details
✅ Troubleshooting section
✅ Security notes
✅ Roadmap for future features
✅ Professional formatting with emojis and tables

Your Instagram Downloader project now has professional documentation! 🎉
