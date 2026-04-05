#!/usr/bin/env python3
"""
Gmail Configuration Diagnostic Tool
Tests your Gmail SMTP connection step by step
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("\n" + "="*70)
print("🧪 GMAIL CONFIGURATION DIAGNOSTIC")
print("="*70)

# Step 1: Check .env file
print("\n📋 STEP 1: Checking .env Configuration")
print("-" * 70)

mail_username = os.getenv('MAIL_USERNAME')
mail_password = os.getenv('MAIL_PASSWORD')
mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
mail_port = os.getenv('MAIL_PORT', '587')
mail_use_tls = os.getenv('MAIL_USE_TLS', 'True')

print(f"   MAIL_USERNAME: {mail_username if mail_username else '❌ NOT SET'}")
print(f"   MAIL_PASSWORD: {'✅ SET' if mail_password else '❌ NOT SET'}")
if mail_password:
    print(f"      Length: {len(mail_password)} characters")
    print(f"      Has spaces: {'❌ YES (BAD!)' if ' ' in mail_password else '✅ NO (Good)'}")
print(f"   MAIL_SERVER: {mail_server}")
print(f"   MAIL_PORT: {mail_port}")
print(f"   MAIL_USE_TLS: {mail_use_tls}")

if not mail_username or not mail_password:
    print("\n❌ EMAIL NOT CONFIGURED!")
    print("   Please check your .env file and make sure MAIL_USERNAME and MAIL_PASSWORD are set.")
    sys.exit(1)

# Step 2: Test SMTP connection
print("\n📋 STEP 2: Testing SMTP Connection")
print("-" * 70)

try:
    import smtplib
    print(f"   Connecting to {mail_server}:{mail_port}...")
    
    server = smtplib.SMTP(mail_server, int(mail_port), timeout=10)
    print(f"   ✅ Connected!")
    
    print(f"   Starting TLS...")
    server.starttls()
    print(f"   ✅ TLS started!")
    
    print(f"   Attempting login as {mail_username}...")
    server.login(mail_username, mail_password)
    print(f"   ✅ Login successful!")
    
    server.quit()
    print(f"   ✅ Connection closed cleanly")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"   ❌ AUTHENTICATION FAILED: {e}")
    print(f"\n   💡 Possible causes:")
    print(f"      - Wrong Gmail app password")
    print(f"      - App password has spaces (should not)")
    print(f"      - 2-Step Verification not enabled on Google Account")
    print(f"      - Gmail blocking the login")
    sys.exit(1)
    
except smtplib.SMTPException as e:
    print(f"   ❌ SMTP ERROR: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ CONNECTION ERROR: {e}")
    print(f"\n   💡 Possible causes:")
    print(f"      - Network/firewall blocking port 587")
    print(f"      - Wrong SMTP server address")
    print(f"      - Timeout (no response from server)")
    sys.exit(1)

# Step 3: Test Flask-Mail
print("\n📋 STEP 3: Testing Flask-Mail")
print("-" * 70)

try:
    from flask import Flask
    from flask_mail import Mail, Message
    
    app = Flask(__name__)
    app.config['MAIL_SERVER'] = mail_server
    app.config['MAIL_PORT'] = int(mail_port)
    app.config['MAIL_USE_TLS'] = mail_use_tls.lower() == 'true'
    app.config['MAIL_USERNAME'] = mail_username
    app.config['MAIL_PASSWORD'] = mail_password
    app.config['MAIL_DEFAULT_SENDER'] = 'noreply@qrauth.com'
    
    mail = Mail(app)
    
    print(f"   Flask-Mail configured ✅")
    print(f"   Attempting to send test email...")
    
    with app.app_context():
        msg = Message(
            subject='🧪 Test from QR Auth System',
            recipients=[mail_username],
            body='This is a test email from the QR Auth System.',
            html='<h1>Test Email</h1><p>If you received this, your email setup is working! ✅</p>'
        )
        mail.send(msg)
    
    print(f"   ✅ Test email sent successfully!")
    print(f"\n   Check your inbox at {mail_username} for the test email!")
    
except Exception as e:
    import traceback
    print(f"   ❌ ERROR: {e}")
    print(f"\n   📋 Full traceback:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED! Your email configuration is working!")
print("="*70 + "\n")
