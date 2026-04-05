# 🚀 Quick Start Guide

## ⚡ Get Running in 2 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Application
```bash
python app.py
```

### 3. Open in Browser
```
http://localhost:5000
```

## 📝 First-Time Setup

### Create Your Account
1. Click **"Register here"** link
2. Fill in username, email, and password
3. Click **Register**

### Login with QR
1. Enter your credentials
2. Click **Login**
3. On another browser/device (or same device):
   - Click **"Start Scanner"**
   - Allow camera permission
   - Scan the displayed QR code
4. ✅ You're logged in!

### Setup 2FA (Optional)
1. Go to **Dashboard**
2. Click **"Enable 2FA"** under Security Settings
3. Scan with **Google Authenticator** or similar app
4. Enter the 6-digit code
5. 🔐 Your account is now protected!

## 🔧 Common Commands

```bash
# Run the app
python app.py

# Stop the app
Ctrl + C

# Fresh database (if needed)
# Delete secure_qr_auth.db and restart app
```

## 🎯 Key Features to Try

✅ Register & Login
✅ QR Code Scanning (try on phone/tablet)
✅ Enable 2FA
✅ Manage Trusted Devices
✅ View Dashboard

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5000 in use | Change port in app.py last line or wait |
| Camera not working | Check browser permissions |
| Can't scan QR | Good lighting + hold still |
| 2FA won't work | Sync device time |

## 📚 Next Steps

- Read [README.md](README.md) for complete documentation
- Check [Security](README.md#security-features) section
- Review [API Endpoints](README.md#api-endpoints)
- Explore dashboard features

---

**You're all set! Happy authenticating! 🔐**
