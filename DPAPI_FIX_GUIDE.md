# 🔧 FIX FOR WINDOWS DPAPI ERROR

## The Problem
Chrome on Windows encrypts cookies with DPAPI (Data Protection API).
yt-dlp cannot decrypt these cookies - this is a known Windows bug.

## ✅ SOLUTION: Export Cookies to File

You have 3 options:

---

## 🎯 OPTION 1: Chrome Extension (EASIEST - 2 minutes)

### Step 1: Install Extension
Visit: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

Click "Add to Chrome"

### Step 2: Login to Instagram
1. Go to instagram.com in Chrome
2. Make sure you're logged in

### Step 3: Export Cookies
1. Click the extension icon (puzzle piece in Chrome toolbar)
2. Find "Get cookies.txt LOCALLY"
3. Click it
4. Click "Export" or "Download"
5. Save the file as **cookies.txt**

### Step 4: Move File
Move **cookies.txt** to your project folder:
```
D:\Instagram_video_downloader\cookies.txt
```

### Step 5: Run App
```bash
python app_with_cookies.py
```

**Done!** ✅

---

## 🎯 OPTION 2: Firefox (No DPAPI Issue)

### Step 1: Install Firefox
If you don't have Firefox, download from: https://www.mozilla.org/firefox/

### Step 2: Login to Instagram in Firefox
1. Open Firefox
2. Go to instagram.com
3. Login to your account

### Step 3: Use Firefox Cookies
Update line 38 in app_with_cookies.py:
```python
# Change from Chrome to Firefox
'--cookies-from-browser', 'firefox',
```

### Step 4: Run App
```bash
python app_with_cookies.py
```

**Firefox doesn't have DPAPI issues!** ✅

---

## 🎯 OPTION 3: Try Without Cookies (Limited)

Sometimes works for very public accounts:

```bash
python app_with_cookies.py
```

Just try pasting Instagram URLs. May work for ~30-40% of public posts.

---

## 📋 Current Setup Instructions

1. **Install Chrome Extension:**
   https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. **Export cookies from instagram.com**

3. **Save as cookies.txt in:**
   ```
   D:\Instagram_video_downloader\cookies.txt
   ```

4. **Run:**
   ```bash
   python app_with_cookies.py
   ```

5. **Visit:**
   http://localhost:5000

---

## 🔍 Verify Cookie Export

After exporting, your cookies.txt should look like:
```
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	...	sessionid	...
.instagram.com	TRUE	/	TRUE	...	csrftoken	...
```

If it looks like this, you're good! ✅

---

## 🐛 Still Not Working?

**Check cookies.txt location:**
```bash
# Should be in same folder as app_with_cookies.py
dir cookies.txt
```

**Check file size:**
```bash
# Should be 5-20 KB
# If 0 KB or 1 KB, export failed
```

**Try this command:**
```bash
yt-dlp --cookies cookies.txt --dump-json --skip-download "INSTAGRAM_URL"
```

If this works, the app will work too!

---

## 💡 Why This Happens

- **Windows 10/11** encrypts Chrome cookies with DPAPI
- **yt-dlp** cannot decrypt DPAPI on some systems
- **Solution:** Export to plain text file
- **Or use:** Firefox (no encryption issue)

---

## 🚀 Quick Commands

```bash
# 1. Check yt-dlp version
yt-dlp --version

# 2. Test with exported cookies
yt-dlp --cookies cookies.txt --get-url "https://www.instagram.com/reel/DP1X37nEsKd/"

# 3. If works, run app
python app_with_cookies.py
```

---

Your Instagram downloader will work perfectly once cookies are exported! 🎉
