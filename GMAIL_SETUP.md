# 📧 Gmail Setup for QR Code Email Delivery

This guide helps you configure Gmail to send QR codes via email for login verification.

## 🔧 Step-by-Step Setup

### Step 1: Enable 2-Step Verification

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Look for "How you sign in to Google"
3. Click on **"2-Step Verification"**
4. Follow the verification process
5. Complete the setup

### Step 2: Generate Gmail App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - (You need 2-Step Verification enabled first)
2. Select:
   - **App**: `Mail`
   - **Device**: `Windows PC` (or your operating system)
3. Click **Generate**
4. Google will show a 16-character password
5. **Copy this password** (you'll need it in Step 4)

### Step 3: Create .env File

Create a file named `.env` in your project root:

```bash
# Copy this and save as .env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
MAIL_DEFAULT_SENDER=noreply@qrauth.com
```

**Replace:**
- `your-email@gmail.com` → Your actual Gmail address
- `xxxx-xxxx-xxxx-xxxx` → The 16-character password from Step 2

### Step 4: Install Email Package

```bash
pip install Flask-Mail
# Or reinstall all dependencies
pip install -r requirements.txt
```

### Step 5: Test the Configuration

```bash
python app.py
```

1. Register a new user
2. Try logging in
3. Check if you receive an email from `noreply@qrauth.com`

---

## ✅ Verification Checklist

- [ ] 2-Step Verification enabled on Google Account
- [ ] App Password generated (16 characters)
- [ ] `.env` file created with correct email and password
- [ ] Flask-Mail installed
- [ ] Test email received successfully

---

## 🔍 Troubleshooting

### "Module not found: flask_mail"
```bash
pip install Flask-Mail
pip install -r requirements.txt
```

### "SMTP Authentication Failed"
- Check your email address is correct
- Check the 16-character app password is correct
- Make sure it's the **App Password**, not your Google password
- Make sure 2-Step Verification is enabled

### "Email not received"
1. Check spam/promotions folder
2. Check that `MAIL_USERNAME` matches your Gmail account
3. Try resending with the "Resend Email" button
4. Check Flask app logs for errors

### "Connection timeout"
- Check your internet connection
- Try a different network
- Gmail SMTP might be temporarily unavailable

### "SSL/TLS Error"
Make sure `MAIL_USE_TLS=True` in your `.env` file

---

## 📱 How It Works After Setup

1. User enters credentials
2. System generates encrypted QR code
3. **Email sent to user** with QR code
4. User checks email
5. User scans QR with trusted device
6. Login complete ✅

---

## 🔐 Security Notes

- **Never** commit `.env` file to git
- `.env` is already in `.gitignore` (ignore it!)
- The App Password is only for this app
- You can revoke it anytime from Google settings
- Use strong Gmail passwords

---

## 🆘 Still Having Issues?

1. Check the `.env` file exists in project root
2. Make sure all values are correct
3. Try creating a fresh `.env` from `.env.example`
4. Check Flask app terminal for error messages
5. Restart the Flask app

---

**Your email QR authentication is now ready! 🎉**
