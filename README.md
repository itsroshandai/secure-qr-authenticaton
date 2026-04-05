# 🔐 Secure QR Authentication System

A production-ready cybersecurity authentication system built with Python Flask that implements multi-factor authentication using QR codes and two-factor authentication (2FA).

## 🌟 Features

- ✅ **User Registration & Authentication** - Secure user registration with password hashing
- ✅ **QR Code-Based Login** - Generate QR codes for secure login verification
- ✅ **Web-Based QR Scanning** - Built-in QR scanner in the browser (no app required)
- ✅ **Trusted Device Management** - Remember and manage trusted devices
- ✅ **Two-Factor Authentication (2FA)** - TOTP-based 2FA using authenticator apps
- ✅ **Session Management** - Secure session handling with expiry
- ✅ **Encryption** - Fernet encryption for secure data transmission
- ✅ **SQLite Database** - Persistent user and device storage
- ✅ **Beautiful UI** - Modern, responsive design with gradient themes

## 📋 Project Structure

```
cybersecurity/
├── app.py                 # Main Flask application
├── crypto_utils.py        # Encryption utilities
├── requirements.txt       # Python dependencies
├── templates/
│   ├── login.html         # Login page
│   ├── register.html      # User registration
│   ├── qr.html            # QR verification (deprecated, use qr_verify.html)
│   ├── qr_verify.html     # QR code verification with scanner
│   ├── dashboard.html     # User dashboard
│   ├── setup_2fa.html     # 2FA setup page
│   └── error.html         # Error page
├── secure_qr_auth.db      # SQLite database (auto-created)
└── README.md              # This file
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone/Extract the Project

```bash
cd cybersecurity
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## 🚀 Usage Guide

### Creating an Account

1. Navigate to **Register** page
2. Enter username, email, password
3. Click **Register**

### Logging In (QR Method)

1. Go to **Login** page
2. Enter credentials
3. You'll be redirected to QR verification page
4. On a trusted device, click **Start Scanner**
5. Allow camera access
6. Scan the displayed QR code
7. Authentication successful! You'll be logged in

### Setting Up 2FA

1. Log in to your account
2. Go to Dashboard → Security Settings
3. Click **Enable 2FA**
4. Scan the QR code with your authenticator app:
   - Google Authenticator
   - Microsoft Authenticator
   - Authy
   - LastPass Authenticator
5. Enter the 6-digit code to verify
6. 2FA is now enabled! 🔐

### Managing Trusted Devices

1. Visit Dashboard
2. Scroll to "Trusted Devices" section
3. View all devices that have scanned your QR code
4. Click **Remove** to untrust a device

## 🔒 Security Features

### Encryption

- All session data is encrypted using Fernet symmetric encryption
- QR codes contain encrypted session IDs
- Passwords are hashed using werkzeug security

### Session Management

- Sessions expire after 5 minutes during login
- 2FA session requires QR verification first
- Automatic session cleanup

### Device Tracking

- Each device gets a unique ID
- IP addresses and user agents are logged
- Last used timestamp for audit trails

### Two-Factor Authentication

- Time-based One-Time Password (TOTP)
- Compatible with standard authenticator apps
- 30-second time windows

## 📊 Database Schema

### Users Table
```sql
- id (PK)
- username (UNIQUE)
- email (UNIQUE)
- password_hash
- two_fa_enabled
- two_fa_secret
- created_at
```

### TrustedDevices Table
```sql
- id (PK)
- user_id (FK)
- device_id (UNIQUE)
- device_name
- user_agent
- ip_address
- last_used
- created_at
- is_active
```

### AuthSessions Table
```sql
- id (PK)
- user_id (FK)
- session_id (UNIQUE)
- encrypted_data
- qr_verified
- qr_scanned_device_id
- created_at
- expires_at
- two_fa_verified
```

## 🔌 API Endpoints

### Authentication Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page redirect |
| `/register` | GET, POST | User registration |
| `/login` | GET, POST | User login |
| `/qr_verify` | GET | QR verification page |
| `/api/scan_qr` | POST | Verify QR scan |
| `/api/check_auth_status/<session_id>` | GET | Check authentication status |
| `/verify_2fa` | POST | Verify 2FA code |
| `/complete_login/<session_id>` | GET | Complete login |

### User Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/dashboard` | GET | User dashboard |
| `/setup_2fa` | GET | 2FA setup page |
| `/confirm_2fa` | POST | Confirm 2FA setup |
| `/remove_device/<device_id>` | POST | Remove trusted device |
| `/logout` | GET | User logout |

## 🧪 Testing the System

### Test Credentials

After starting, the database will be created. You can:

1. Register a new user through the web interface
2. Test the QR scanning with multiple devices
3. Enable 2FA and test with an authenticator app

### Test Flow

```
1. Register → 2. Login → 3. Scan QR → 4. Optional 2FA → 5. Dashboard
```

## 🔑 Environment Variables

Create a `.env` file if you want to customize settings:

```env
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///secure_qr_auth.db
SECRET_KEY=your-secret-key-here
```

## 📱 Browser Compatibility

- ✅ Chrome/Chromium (Full support)
- ✅ Firefox (Full support)
- ✅ Safari (Full support)
- ✅ Edge (Full support)
- ⚠️ Mobile browsers (Requires HTTPS for camera access)

## ⚠️ Important Notes for Production

1. **Change the SECRET_KEY** in `app.py` (currently auto-generated)
2. **Use HTTPS** - Required for camera access in production
3. **Database** - Consider using PostgreSQL instead of SQLite
4. **Environment Variables** - Use `.env` file for sensitive data
5. **Password Policy** - Implement stronger password requirements
6. **Rate Limiting** - Add rate limiting for brute force protection
7. **CSRF Protection** - Enable CSRF tokens in forms
8. **Logging** - Set up audit logging for security events

## 🐛 Troubleshooting

### Camera Not Working

- Check if browser has camera permission
- On HTTPS sites, camera is more reliable
- Try allowing camera access explicitly

### QR Code Won't Scan

- Ensure QR code is clearly visible
- Good lighting is important
- Keep QR code within frame bounds

### 2FA Code Invalid

- Check your device's time is synchronized
- 2FA codes expire after 30 seconds
- Try the next code if at boundary

### Database Locked

- Close other connections to the database
- Try restarting the Flask application
- Delete `secure_qr_auth.db` and restart (data will be lost)

## 📚 Dependencies

- **Flask** - Web framework
- **Flask-SQLAlchemy** - ORM for database
- **Flask-Login** - User session management
- **qrcode** - QR code generation
- **cryptography (Fernet)** - Encryption
- **pyotp** - TOTP 2FA implementation
- **Pillow** - Image processing
- **werkzeug** - Security utilities

## 🔐 Security Best Practices Implemented

1. **Password Hashing** - Using werkzeug security
2. **Session Expiry** - 5-minute session timeout
3. **Encryption** - Fernet symmetric encryption
4. **Device Tracking** - Audit trail of device access
5. **TOTP 2FA** - Time-based one-time passwords
6. **Database Indexing** - Optimized lookups

## 📝 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

Feel free to extend this project with:

- Email verification
- SMS OTP option
- Biometric authentication
- Social login integration
- WebAuthn/FIDO2 support
- Advanced analytics dashboard

## 🎯 Future Enhancements

- [ ] Email verification on registration
- [ ] Password reset via email
- [ ] SMS-based 2FA
- [ ] WebAuthn support
- [ ] Admin dashboard
- [ ] Audit logging
- [ ] Login history
- [ ] Geolocation alerts
- [ ] Suspicious activity detection

## 📧 Support

For issues or questions, check the code comments or refer to the respective library documentation:

- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- pyotp: https://github.com/pyca/pyotp
- qrcode: https://github.com/lincolnloop/python-qrcode

---

**Happy Secure Coding! 🔒**
