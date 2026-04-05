from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from io import BytesIO
import base64
import uuid
import json
import time
from datetime import datetime, timedelta
from crypto_utils import encrypt_data, decrypt_data
import pyotp
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

# Flask Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secure_qr_auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@qrauth.com')

# Database
db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    two_fa_enabled = db.Column(db.Boolean, default=False)
    two_fa_secret = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    devices = db.relationship('TrustedDevice', backref='user', lazy=True, cascade='all, delete-orphan')
    sessions = db.relationship('AuthSession', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def enable_2fa(self):
        self.two_fa_secret = pyotp.random_base32()
        self.two_fa_enabled = True
        return pyotp.totp.TOTP(self.two_fa_secret).provisioning_uri(
            name=self.email, issuer_name='Secure QR Auth'
        )

    def verify_2fa(self, token):
        if not self.two_fa_enabled:
            return False
        totp = pyotp.TOTP(self.two_fa_secret)
        return totp.verify(token)


class TrustedDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.String(255), unique=True, nullable=False)
    device_name = db.Column(db.String(120), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class AuthSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    encrypted_data = db.Column(db.String(500), nullable=False)
    qr_verified = db.Column(db.Boolean, default=False)
    qr_scanned_device_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    two_fa_verified = db.Column(db.Boolean, default=False)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== UTILITY FUNCTIONS ====================

def get_client_id():
    """Generate or retrieve device/client ID"""
    device_id = request.cookies.get('device_id')
    if not device_id:
        device_id = str(uuid.uuid4())
    return device_id


def generate_qr_code(data):
    """Generate QR code image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str


def generate_qr_image_bytes(data):
    """Generate QR code as image bytes for email attachment"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def send_qr_email(user_email, username, session_id, qr_image_data):
    """Send QR code to user's email for verification"""
    # Check if email is properly configured
    if not os.getenv('MAIL_USERNAME') or not os.getenv('MAIL_PASSWORD'):
        print(f"⚠️  Email not configured. Skipping email send.")
        return False
    
    try:
        print(f"\n{'='*70}")
        print(f"📧 SENDING EMAIL")
        print(f"{'='*70}")
        print(f"   To: {user_email}")
        print(f"   From: {os.getenv('MAIL_USERNAME')}")
        
        verification_link = url_for('qr_display', session_id=session_id, _external=True)
        
        # Create message with simple HTML
        msg = Message(
            subject='🔐 Your Secure Login QR Code - Verify in 5 Minutes',
            recipients=[user_email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div style="background: white; margin: 20px; border-radius: 12px; padding: 40px; text-align: center;">
                    <h1 style="color: #333; font-size: 28px; margin-bottom: 10px;">🔐 Login Verification</h1>
                    <p style="color: #888; font-size: 16px;">Hi <strong>{username}</strong>,</p>
                    
                    <div style="background: #f0f4ff; border: 2px solid #667eea; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <p style="color: #333; font-weight: 600;">Your login QR code is ready!</p>
                        <p style="color: #666; font-size: 14px;">Click the button below to view and scan your QR code:</p>
                    </div>
                    
                    <a href="{verification_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 40px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; margin: 20px 0;">📱 View QR Code</a>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px;">
                        <strong>⏰ Session expires in 5 minutes</strong><br>
                        🔒 Never share this email with anyone. If you didn't request this login, ignore this email.
                    </p>
                    
                    <footer style="color: #bbb; font-size: 11px; margin-top: 20px;">
                        Secure QR Authentication System © 2026
                    </footer>
                </div>
            </div>
            """
        )
        
        print(f"   📨 Sending via: {app.config.get('MAIL_SERVER')}:{app.config.get('MAIL_PORT')}")
        
        # Send the email
        mail.send(msg)
        
        print(f"   ✅ Email sent successfully!")
        print(f"{'='*70}\n")
        return True
        
    except Exception as e:
        import traceback
        error_msg = f"❌ ERROR: {str(e)}"
        
        print(f"   {error_msg}")
        print(f"\n   📋 Error Type: {type(e).__name__}")
        print(f"   📋 Traceback:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                print(f"      {line}")
        print(f"{'='*70}\n")
        
        # Log to file for debugging
        try:
            with open('email_errors.log', 'a') as log_file:
                log_file.write(f"\n{error_msg}\n")
                log_file.write(traceback.format_exc())
        except:
            pass
        
        return False


# ==================== ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, email, password, confirm_password]):
            return render_template('register.html', error='All fields required'), 400

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match'), 400

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists'), 400

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already exists'), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login')), 302
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            return render_template('login.html', error='Invalid credentials'), 401

        # Create auth session
        session_id = str(uuid.uuid4())
        session_data = {
            'user_id': user.id,
            'username': user.username,
            'created_at': datetime.utcnow().isoformat()
        }
        
        encrypted = encrypt_data(json.dumps(session_data))
        
        auth_session = AuthSession(
            user_id=user.id,
            session_id=session_id,
            encrypted_data=encrypted,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        db.session.add(auth_session)
        db.session.commit()

        # Generate QR code data
        qr_data = encrypt_data(json.dumps({
            'session_id': session_id,
            'timestamp': time.time()
        }))
        
        # Generate QR image bytes for email attachment
        qr_image_bytes = generate_qr_image_bytes(qr_data)

        # Try to send email if configured
        if os.getenv('MAIL_USERNAME') and os.getenv('MAIL_PASSWORD'):
            # Email configured - attempt to send
            email_sent = send_qr_email(user.email, user.username, session_id, qr_image_bytes)
            if email_sent:
                print(f"✅ Email sent successfully - user will check inbox")
            else:
                print(f"⚠️  Email failed - will show QR on verification page instead")
        else:
            print(f"🎯 Email not configured - will show QR on verification page")
        
        # Store session info
        session['temp_session_id'] = session_id
        session['temp_user_id'] = user.id
        session['requires_2fa'] = user.two_fa_enabled
        
        # Always redirect to qr_verify - QR will be displayed as fallback if email failed
        return redirect(url_for('qr_verify', session_id=session_id))

    return render_template('login.html')


@app.route('/check_email')
def check_email():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return redirect(url_for('login'))
    
    auth_session = AuthSession.query.filter_by(session_id=session_id).first()
    
    if not auth_session or auth_session.is_expired():
        return render_template('error.html', message='Session expired. Please login again.')
    
    return render_template('check_email.html', session_id=session_id)


@app.route('/qr_display/<session_id>')
def qr_display(session_id):
    """Display the QR code for scanning"""
    auth_session = AuthSession.query.filter_by(session_id=session_id).first()
    
    if not auth_session or auth_session.is_expired():
        return render_template('error.html', message='Session expired. Please login again.')
    
    # Generate QR code for display
    qr_data = encrypt_data(json.dumps({
        'session_id': session_id,
        'timestamp': time.time()
    }))
    qr_image = generate_qr_code(qr_data)
    device_id = get_client_id()
    
    return render_template('qr_display.html', session_id=session_id, device_id=device_id, qr_image=qr_image)


@app.route('/qr_verify')
def qr_verify():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return redirect(url_for('login'))

    auth_session = AuthSession.query.filter_by(session_id=session_id).first()
    
    if not auth_session or auth_session.is_expired():
        return render_template('error.html', message='Session expired. Please login again.')

    device_id = get_client_id()

    # QR comes from email - verification page only has scan/upload options
    return render_template('qr_verify.html', session_id=session_id, device_id=device_id)


@app.route('/api/scan_qr', methods=['POST'])
def scan_qr():
    """Endpoint for trusted device to scan and verify QR"""
    data = request.get_json()
    session_id = data.get('session_id')
    device_id = data.get('device_id')
    device_name = data.get('device_name', 'Unknown Device')

    auth_session = AuthSession.query.filter_by(session_id=session_id).first()

    if not auth_session or auth_session.is_expired():
        return jsonify({'success': False, 'message': 'Session expired'}), 401

    if auth_session.qr_verified:
        return jsonify({'success': False, 'message': 'QR already verified'}), 400

    # Mark QR as verified
    auth_session.qr_verified = True
    auth_session.qr_scanned_device_id = device_id

    # Add device as trusted
    existing_device = TrustedDevice.query.filter_by(device_id=device_id).first()
    if not existing_device:
        trusted_device = TrustedDevice(
            user_id=auth_session.user_id,
            device_id=device_id,
            device_name=device_name,
            user_agent=request.headers.get('User-Agent', 'Unknown'),
            ip_address=request.remote_addr
        )
        db.session.add(trusted_device)
    else:
        existing_device.last_used = datetime.utcnow()

    db.session.commit()

    return jsonify({'success': True, 'message': 'QR verified successfully'})


@app.route('/api/check_auth_status/<session_id>')
def check_auth_status(session_id):
    """Check if QR has been verified"""
    auth_session = AuthSession.query.filter_by(session_id=session_id).first()

    if not auth_session:
        return jsonify({'authenticated': False, 'message': 'Session not found'}), 404

    if auth_session.is_expired():
        return jsonify({'authenticated': False, 'message': 'Session expired'})

    if not auth_session.qr_verified:
        return jsonify({'authenticated': False, 'message': 'Waiting for QR scan'})

    # Check if 2FA is required
    user = User.query.get(auth_session.user_id)
    if user.two_fa_enabled and not auth_session.two_fa_verified:
        return jsonify({
            'authenticated': False,
            'requires_2fa': True,
            'message': 'Enter 2FA code'
        })

    # Authentication successful
    return jsonify({'authenticated': True, 'message': 'Authentication successful'})


@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    """Verify 2FA code"""
    data = request.get_json()
    session_id = data.get('session_id')
    code = data.get('code')

    auth_session = AuthSession.query.filter_by(session_id=session_id).first()

    if not auth_session or not auth_session.qr_verified:
        return jsonify({'success': False, 'message': 'Invalid session'}), 400

    user = User.query.get(auth_session.user_id)

    if not user.verify_2fa(code):
        return jsonify({'success': False, 'message': 'Invalid 2FA code'}), 401

    auth_session.two_fa_verified = True
    db.session.commit()

    return jsonify({'success': True, 'message': '2FA verified'})


@app.route('/complete_login/<session_id>')
def complete_login(session_id):
    """Complete login after QR verification and optional 2FA"""
    auth_session = AuthSession.query.filter_by(session_id=session_id).first()

    if not auth_session:
        return redirect(url_for('login'))

    if auth_session.is_expired():
        return render_template('error.html', message='Session expired. Please login again.')

    if not auth_session.qr_verified:
        return render_template('error.html', message='QR not verified.')

    user = User.query.get(auth_session.user_id)

    if user.two_fa_enabled and not auth_session.two_fa_verified:
        return render_template('error.html', message='2FA not verified.')

    # Login successful
    login_user(user, remember=True)
    session.pop('temp_session_id', None)
    session.pop('temp_user_id', None)
    session.pop('requires_2fa', None)

    return redirect(url_for('dashboard'))


@app.route('/test_email')
def test_email():
    """Test email configuration - for debugging only"""
    try:
        print("\n" + "="*60)
        print("🧪 TESTING EMAIL CONFIGURATION")
        print("="*60)
        
        # Check configuration
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')
        mail_server = app.config.get('MAIL_SERVER')
        mail_port = app.config.get('MAIL_PORT')
        mail_use_tls = app.config.get('MAIL_USE_TLS')
        
        print(f"\n📧 Configuration:")
        print(f"   - MAIL_SERVER: {mail_server}")
        print(f"   - MAIL_PORT: {mail_port}")
        print(f"   - MAIL_USE_TLS: {mail_use_tls}")
        print(f"   - MAIL_USERNAME: {mail_username if mail_username else '❌ NOT SET'}")
        print(f"   - MAIL_PASSWORD: {'✅ SET' if mail_password else '❌ NOT SET'}")
        
        if not mail_username or not mail_password:
            msg = "❌ Email not configured! Check your .env file."
            print(f"\n{msg}\n")
            return msg, 400
        
        # Send test email
        print(f"\n📤 Sending test email to {mail_username}...")
        
        test_msg = Message(
            subject='🧪 Test Email - QR Auth System',
            recipients=[mail_username],
            body='This is a test email to verify your Gmail configuration is working correctly. If you received this, your email setup is working! ✅',
            html='''
            <div style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
                <div style="background: white; border-radius: 8px; padding: 30px; text-align: center;">
                    <h1 style="color: #667eea;">🧪 Test Email</h1>
                    <p style="color: #666; font-size: 16px;">This is a test email to verify your Gmail configuration is working correctly.</p>
                    <div style="background: #e8f5e9; border: 2px solid #4caf50; border-radius: 5px; padding: 15px; margin: 20px 0;">
                        <p style="color: #2e7d32; font-weight: bold;">✅ If you received this, your email setup is working!</p>
                    </div>
                    <p style="color: #999; font-size: 12px;">Sent from Secure QR Auth System</p>
                </div>
            </div>
            '''
        )
        
        mail.send(test_msg)
        
        msg = f"✅ Test email sent successfully to {mail_username}! Check your inbox."
        print(f"\n{msg}\n")
        print("="*60 + "\n")
        return msg, 200
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Error sending test email: {str(e)}"
        print(f"\n{error_msg}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "="*60 + "\n")
        return error_msg, 500


@app.route('/dashboard')
@login_required
def dashboard():
    devices = TrustedDevice.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, devices=devices)


@app.route('/setup_2fa')
@login_required
def setup_2fa():
    if current_user.two_fa_enabled:
        return redirect(url_for('dashboard'))

    provisioning_uri = current_user.enable_2fa()
    db.session.commit()

    qr_image = generate_qr_code(provisioning_uri)
    return render_template('setup_2fa.html', qr_image=qr_image, secret=current_user.two_fa_secret)


@app.route('/confirm_2fa', methods=['POST'])
@login_required
def confirm_2fa():
    code = request.form.get('code')

    if not current_user.verify_2fa(code):
        return render_template('setup_2fa.html', error='Invalid code', 
                             qr_image=generate_qr_code(pyotp.totp.TOTP(current_user.two_fa_secret).provisioning_uri(
                                 name=current_user.email, issuer_name='Secure QR Auth'
                             )))

    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/remove_device/<int:device_id>', methods=['POST'])
@login_required
def remove_device(device_id):
    device = TrustedDevice.query.filter_by(id=device_id, user_id=current_user.id).first()

    if device:
        db.session.delete(device)
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/api/resend_qr_email', methods=['POST'])
def resend_qr_email():
    """Resend QR code to user's email"""
    data = request.get_json()
    session_id = data.get('session_id')

    auth_session = AuthSession.query.filter_by(session_id=session_id).first()

    if not auth_session or auth_session.is_expired():
        return jsonify({'success': False, 'message': 'Session expired'}), 401

    user = User.query.get(auth_session.user_id)

    # Regenerate QR code
    qr_data = encrypt_data(json.dumps({
        'session_id': session_id,
        'timestamp': time.time()
    }))
    qr_image = generate_qr_code(qr_data)

    # Send email
    email_sent = send_qr_email(user.email, user.username, session_id, qr_image)

    if email_sent:
        return jsonify({'success': True, 'message': 'Email resent'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send email'}), 500


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message='Page not found'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', message='Server error'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Print startup diagnostics
        print("\n" + "="*70)
        print("🚀 SECURE QR AUTH SYSTEM - STARTUP DIAGNOSTICS")
        print("="*70)
        
        # Check Flask-Mail Configuration
        print("\n📧 EMAIL CONFIGURATION:")
        mail_username = os.getenv('MAIL_USERNAME')
        mail_password = os.getenv('MAIL_PASSWORD')
        mail_server = app.config.get('MAIL_SERVER')
        mail_port = app.config.get('MAIL_PORT')
        mail_use_tls = app.config.get('MAIL_USE_TLS')
        
        if mail_username:
            print(f"   ✅ MAIL_USERNAME: {mail_username}")
        else:
            print(f"   ❌ MAIL_USERNAME: NOT SET")
            
        if mail_password:
            print(f"   ✅ MAIL_PASSWORD: SET ({len(mail_password)} chars)")
        else:
            print(f"   ❌ MAIL_PASSWORD: NOT SET")
            
        print(f"   📍 MAIL_SERVER: {mail_server}")
        print(f"   🔌 MAIL_PORT: {mail_port}")
        print(f"   🔒 MAIL_USE_TLS: {mail_use_tls}")
        
        if mail_username and mail_password:
            print("\n   ✅ Email configuration looks good!")
            print(f"   📧 Test email endpoint: http://localhost:5000/test_email")
        else:
            print("\n   ⚠️  Email not configured. Follow GMAIL_SETUP.md for setup.")
        
        print("\n" + "="*70)
        print("🎯 Application Started Successfully!")
        print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)