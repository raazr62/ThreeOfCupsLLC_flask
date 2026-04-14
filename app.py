from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
import os
import json
import re
import statistics
import secrets
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail
from dotenv import load_dotenv
from models import db, User, Assessment, ReviewerAssessment, Match, Event, EventRSVP, EventCheckIn, EventEnergyExchange, EventMatchmakingDraft, EventUserBoardPosition, EventBoardCard
from email_helper import send_password_reset_email, send_match_notification_email, send_verification_email, send_email_change_notification, send_email_change_verification, send_walk_in_welcome_email, send_rsvp_admin_notification, send_rsvp_cancellation_admin_notification
from security_utils import (
    sanitize_input, sanitize_email, sanitize_username,
    sanitize_location, sanitize_json_data, setup_template_filters,
    validate_file_upload
)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use environment variable in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///friendship.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Security configurations
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 10800  # 3 hour session timeout

# Email configuration
# NOTE: Update these with your actual email credentials in .env file
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
# Use MAIL_DEFAULT_SENDER if set, otherwise fallback to MAIL_USERNAME
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')
# Force ASCII-safe email handling to prevent encoding issues with strict SMTP servers
app.config['MAIL_ASCII_ATTACHMENTS'] = False

mail = Mail(app)

# Beta access settings
BETA_ACCESS_CODE = 'threeofcups2025foundedbyiris'  # Change this to your desired access code
UNDER_CONSTRUCTION = False  # Set to False when ready to launch

# Reviewer access settings
REVIEWER_ACCESS_CODE = 'threeofcups2025'  # Change this to your desired reviewer access code

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def beta_access_required(f):
    """Decorator to check if user has beta access when site is under construction"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if UNDER_CONSTRUCTION and not session.get('beta_access'):
            return redirect(url_for('coming_soon'))
        return f(*args, **kwargs)
    return decorated_function

def reviewer_access_required(f):
    """Decorator to check if user has reviewer access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('reviewer_access'):
            return redirect(url_for('reviewer_login'))
        return f(*args, **kwargs)
    return decorated_function

def sanitize_email_content(text):
    """
    Aggressively sanitize email content to remove ALL non-ASCII characters for SMTP compatibility.
    This includes Unicode punctuation, emojis, and any other characters that could cause encoding issues.

    Strategy:
    1. First replace common Unicode characters with ASCII equivalents
    2. Then strip any remaining non-ASCII characters (including emojis)
    """
    if not text:
        return text

    # First pass: Replace common Unicode punctuation with ASCII equivalents
    replacements = {
        '\u2014': '--',          # Em dash
        '\u2013': '-',           # En dash
        '\u2018': "'",           # Left single quote
        '\u2019': "'",           # Right single quote
        '\u201c': '"',           # Left double quote
        '\u201d': '"',           # Right double quote
        '\u2026': '...',         # Ellipsis
        '\u2022': '*',           # Bullet point
        '\U0001f31f': '',        # Star emoji 🌟
        '\U0001f4ab': '',        # Dizzy emoji 💫
        '\U0001f493': '',        # Beating heart emoji 💓
        '\U0001f49c': '',        # Purple heart emoji 💜
        '\u2764\ufe0f': '',      # Red heart emoji ❤️
        '\u2764': '',            # Red heart (without variation selector)
    }

    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)

    # Second pass: Aggressively remove any remaining non-ASCII characters
    # This catches any emojis or Unicode characters we didn't explicitly map
    try:
        # Encode to ASCII, replacing any characters that can't be encoded
        text = text.encode('ascii', 'ignore').decode('ascii')
    except Exception as e:
        print(f"Warning: Error during ASCII sanitization: {e}")

    return text

def format_draft_email_to_html(plain_text, bold_words=None, logo_url=None):
    """
    Convert plain text draft email to formatted HTML.
    Section headers and specified words (e.g. names, pronouns) are bolded.
    """
    if not plain_text:
        return ""

    import html

    # Sanitize content to remove all non-ASCII characters for SMTP compatibility
    plain_text = sanitize_email_content(plain_text)

    # Escape HTML
    text = html.escape(plain_text)

    # Bold specified words (names, pronouns) wherever they appear
    if bold_words:
        for word in bold_words:
            if word:
                escaped_word = html.escape(word)
                text = text.replace(escaped_word, f'<strong>{escaped_word}</strong>')

    # Section headers to bold (matched after escaping)
    bold_headers = [
        "Here&#x27;s why I think you two will connect:",
        "Here's why I think you two will connect:",
        "Some fun overlaps:",
        "A gentle awareness:",
        "Next steps:",
        "Contact info:",
        "Here are a few more ideas from the Three of Cups team:",
    ]

    paragraphs = text.split('\n\n')
    html_parts = ['<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">']

    if logo_url:
        html_parts.append(
            f'<div style="background-color: #FF9B9B; width: 100%; padding: 24px 0; text-align: center; margin-bottom: 24px;">'
            f'<img src="{logo_url}" alt="Three of Cups" style="max-height: 80px; display: inline-block;">'
            f'</div>'
        )

    for para in paragraphs:
        if not para.strip():
            continue

        stripped = para.strip()

        # Check if it's a bulleted list
        if '•' in para:
            lines = para.split('\n')
            html_parts.append('<p style="margin: 15px 0; line-height: 1.8;">')
            for line in lines:
                if line.strip():
                    html_parts.append(f'{line.strip()}<br>')
            html_parts.append('</p>')
        else:
            # Bold any matching section headers at the start of the paragraph
            for header in bold_headers:
                if stripped.startswith(header):
                    para = para.replace(header, f'<strong>{header}</strong>', 1)
                    break
            formatted = para.replace('\n', '<br>')
            html_parts.append(f'<p style="margin: 15px 0; line-height: 1.8;">{formatted}</p>')

    html_parts.append('<hr style="border: none; border-top: 2px solid #FF9B9B; margin: 24px 0;">')
    html_parts.append('<p style="margin: 0;"><a href="https://linktr.ee/threeofcupsllc" style="color: #FF9B9B;">follow us for more opportunities to connect!</a></p>')
    html_parts.append('</div>')

    return ''.join(html_parts)

def validate_password(password):
    """
    Validate password meets security requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character (@$!%*?&)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    if not re.search(r'[@$!%*?&]', password):
        return False, "Password must contain at least one special character (@$!%*?&)"

    return True, "Password is valid"

def calculate_age(date_of_birth):
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    today = date.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    return age

def calculate_friendship_scores(assessment_data):
    scores = {
        'emotional_availability': 0,
        'time_energy': 0,
        'communication_skills': 0,
        'commitment_level': 0,
        'social_compatibility': 0
    }
    
    if 'friendship_readiness' not in assessment_data:
        return scores, 0
    
    fr = assessment_data['friendship_readiness']
    
    emotional_questions = ['emotional_energy', 'share_feelings', 'bounce_back', 'interested_others']
    emotional_scores = []
    for q in emotional_questions:
        if q in fr and fr[q]:
            try:
                emotional_scores.append(int(fr[q]))
            except (ValueError, TypeError):
                pass
    
    if emotional_scores:
        scores['emotional_availability'] = int(statistics.mean(emotional_scores) * 20)
    
    time_questions = ['make_time', 'follow_through', 'maintain_effort']
    time_scores = []
    for q in time_questions:
        if q in fr and fr[q]:
            try:
                time_scores.append(int(fr[q]))
            except (ValueError, TypeError):
                pass
    
    if time_scores:
        scores['time_energy'] = int(statistics.mean(time_scores) * 20)
    
    comm_questions = ['good_listener', 'express_needs', 'handle_disagreements']
    comm_scores = []
    for q in comm_questions:
        if q in fr and fr[q]:
            try:
                comm_scores.append(int(fr[q]))
            except (ValueError, TypeError):
                pass
    
    if comm_scores:
        scores['communication_skills'] = int(statistics.mean(comm_scores) * 20)
    
    commitment_questions = ['follow_through', 'maintain_effort']
    commitment_scores = []
    for q in commitment_questions:
        if q in fr and fr[q]:
            try:
                commitment_scores.append(int(fr[q]))
            except (ValueError, TypeError):
                pass
    
    if commitment_scores:
        scores['commitment_level'] = int(statistics.mean(commitment_scores) * 20)
    
    if 'social_preferences' in assessment_data:
        sp = assessment_data['social_preferences']
        social_score = 50
        
        if sp.get('introversion') == '3':
            social_score += 20
        elif sp.get('introversion') in ['2', '4']:
            social_score += 10
        
        if sp.get('group_size') == 'small':
            social_score += 15
        elif sp.get('group_size') == 'medium':
            social_score += 10
        
        scores['social_compatibility'] = min(100, social_score)
    
    overall_score = int(statistics.mean([s for s in scores.values() if s > 0]))
    
    return scores, overall_score

def get_personalized_insights(assessment_data, scores):
    insights = []
    
    if scores['communication_skills'] >= 80:
        insights.append("Your communication style suggests you'd thrive in small group settings")
    
    if scores['time_energy'] < 70:
        insights.append("Consider scheduling regular friend time to improve your availability score")
    
    if scores['emotional_availability'] >= 85:
        insights.append("Your high empathy score indicates you're great at supporting others")
    
    if 'social_preferences' in assessment_data:
        intro_level = assessment_data['social_preferences'].get('introversion')
        if intro_level in ['1', '2']:
            insights.append("Your outgoing nature makes you great at initiating social connections")
        elif intro_level in ['4', '5']:
            insights.append("Your thoughtful approach to relationships leads to deep, meaningful connections")
    
    if not insights:
        insights.append("You show strong potential for building lasting friendships")
    
    return insights

def get_comparative_data():
    all_assessments = Assessment.query.all()
    all_scores = []
    
    for assessment in all_assessments:
        if assessment.answers:
            try:
                data = json.loads(assessment.answers)
                _, overall = calculate_friendship_scores(data)
                if overall > 0:
                    all_scores.append(overall)
            except:
                continue
    
    if not all_scores:
        return {"average": 75, "percentile": 50}
    
    average_score = int(statistics.mean(all_scores))
    return {"average": average_score, "total_users": len(all_scores)}

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Set up template filters for security
setup_template_filters(app)

# Add age calculation filter
@app.template_filter('calculate_age')
def calculate_age_filter(date_of_birth):
    """Template filter to calculate age from date of birth"""
    return calculate_age(date_of_birth)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Security headers middleware
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses."""
    # Content Security Policy - Restrictive policy to prevent XSS
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "  # Tailwind CDN requires inline
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "  # Inline styles for tailwind
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy

    # Additional security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'  # Prevent MIME type sniffing
    response.headers['X-Frame-Options'] = 'DENY'  # Prevent clickjacking
    response.headers['X-XSS-Protection'] = '1; mode=block'  # Enable XSS filter
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'  # Control referrer info

    # HSTS - only in production with HTTPS
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    return response

# Coming Soon page
@app.route('/coming-soon')
def coming_soon():
    return render_template('coming_soon.html')

# Beta access route
@app.route('/beta-access', methods=['POST'])
def beta_access():
    access_code = request.form.get('access_code')
    if access_code == BETA_ACCESS_CODE:
        session['beta_access'] = True
        return redirect(url_for('home'))
    else:
        flash('Invalid access code.')
        return redirect(url_for('coming_soon'))

# Homepage route
@app.route('/')
@beta_access_required
def home():
    return render_template('index.html')

# About route
@app.route('/about')
@beta_access_required
def about():
    return render_template('about.html')

# Services route
@app.route('/services')
@beta_access_required
def services():
    return render_template('services.html')

# Privacy Policy route
@app.route('/privacy')
@beta_access_required
def privacy():
    return render_template('privacy.html')

# Contact route
@app.route('/contact')
@beta_access_required
def contact():
    return render_template('contact.html')

@app.route('/submit-contact', methods=['POST'])
@beta_access_required
def submit_contact():
    contact_name = sanitize_input(request.form.get('contact_name', ''), max_length=200, allow_newlines=False)
    contact_email = sanitize_email(request.form.get('contact_email', ''))
    contact_message = sanitize_input(request.form.get('contact_message', ''), max_length=5000, allow_newlines=True)

    if not contact_name or not contact_email or not contact_message:
        flash('Please fill out all fields.')
        return redirect(url_for('contact'))

    # Send contact form email to admin
    try:
        from flask_mail import Message
        msg = Message(
            subject=f'Contact Form: Message from {contact_name}',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['admin@threeofcupsllc.com'],
            reply_to=contact_email
        )

        msg.body = f"""
Contact Form Submission

From: {contact_name}
Email: {contact_email}

Message:
{contact_message}

---
Submitted on: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
        """

        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #FF9B9B, #FFB88C); padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="color: white; margin: 0;">Contact Form Submission</h2>
            </div>
            <div style="background-color: #FAF7F5; padding: 30px; border-radius: 0 0 8px 8px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #FF9B9B; margin-top: 0;">Contact Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Name:</td>
                            <td style="padding: 8px 0;">{contact_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Email:</td>
                            <td style="padding: 8px 0;"><a href="mailto:{contact_email}" style="color: #FFB88C;">{contact_email}</a></td>
                        </tr>
                    </table>
                </div>

                <div style="background-color: white; padding: 20px; border-radius: 8px;">
                    <h4 style="color: #FFB88C; margin-top: 0;">Message:</h4>
                    <p style="line-height: 1.6; color: #333; white-space: pre-wrap;">{contact_message}</p>
                </div>

                <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
                    Submitted on {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
                </p>
            </div>
        </div>
        """

        mail.send(msg)
        flash('Thank you for reaching out! We\'ll get back to you soon.')
    except Exception as e:
        print(f"Error sending contact form email: {e}")
        flash('There was an issue sending your message. Please try again or email us directly at admin@threeofcupsllc.com')

    return redirect(url_for('contact'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
@beta_access_required
def register():
    if request.method == 'POST':
        # Sanitize all user inputs
        first_name = sanitize_input(request.form.get('first_name', ''), max_length=100, allow_newlines=False)
        last_name = sanitize_input(request.form.get('last_name', ''), max_length=100, allow_newlines=False)
        email = sanitize_email(request.form.get('email', ''))
        username = sanitize_username(request.form.get('username', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        pronouns = sanitize_input(request.form.get('pronouns', ''), max_length=100, allow_newlines=False)
        pronouns_other_text = sanitize_input(request.form.get('pronouns_other_text', ''), max_length=100, allow_newlines=False)
        date_of_birth_str = request.form.get('date_of_birth', '').strip()
        location = sanitize_location(request.form.get('location', ''))

        # If "other" is selected for pronouns, use the custom text
        if pronouns == 'other':
            if not pronouns_other_text:
                flash('Please specify your pronouns.')
                return redirect(url_for('register'))
            pronouns = pronouns_other_text

        # Validate all fields are provided
        if not all([first_name, last_name, email, username, password, confirm_password, pronouns, date_of_birth_str, location]):
            flash('All fields are required.')
            return redirect(url_for('register'))

        # Validate and parse date of birth
        try:
            date_of_birth = datetime.strptime(date_of_birth_str, '%m/%d/%Y').date()
        except ValueError:
            flash('Invalid date of birth format. Please use MM/DD/YYYY.')
            return redirect(url_for('register'))

        # Validate user is at least 18 years old
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        if age < 18:
            flash('You must be at least 18 years old to register.')
            return redirect(url_for('register'))

        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message)
            return redirect(url_for('register'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Check if it's an incomplete profile from walk-in
            if existing_user.profile_incomplete:
                # Always generate a new token and send email
                token = existing_user.generate_profile_completion_token()
                db.session.commit()

                # Send profile completion email
                profile_completion_url = url_for('complete_profile', token=token, _external=True)
                # Get the event they checked into
                latest_checkin = EventCheckIn.query.filter_by(user_id=existing_user.id, is_walk_in=True).order_by(EventCheckIn.checked_in_at.desc()).first()
                event_title = latest_checkin.event.title if latest_checkin else "our event"
                success, error = send_walk_in_welcome_email(mail, app.config['MAIL_DEFAULT_SENDER'], existing_user, event_title, profile_completion_url)

                email_sent = False
                if success:
                    email_sent = True
                else:
                    flash(f'Failed to send profile completion email: {error}', 'error')

                # Render special page for incomplete profile
                return render_template('profile_incomplete.html',
                                     user_email=email,
                                     has_password=False,
                                     email_sent=email_sent)
            else:
                flash('Email already exists.')
                return redirect(url_for('register'))

        # All new registrations are created as regular users (not admin)
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            pronouns=pronouns,
            date_of_birth=date_of_birth,
            location=location,
            is_admin=False
        )
        user.set_password(password)

        # Generate verification token
        token = user.generate_verification_token()

        db.session.add(user)
        db.session.commit()

        # Send verification email
        verification_url = url_for('verify_email', token=token, _external=True)
        send_verification_email(mail, app.config['MAIL_DEFAULT_SENDER'], user, verification_url)

        # Log in the user immediately
        login_user(user)

        # Check if user has already completed an assessment
        existing_assessment = Assessment.query.filter_by(user_id=user.id).first()
        if existing_assessment:
            return redirect(url_for('user_dashboard'))
        else:
            return redirect(url_for('assessment'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
@beta_access_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        # Sanitize login input
        username_or_email = sanitize_input(request.form.get('username', ''), max_length=150, allow_newlines=False)
        password = request.form.get('password', '')

        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user:
            # Check if user has incomplete profile (walk-in user)
            if user.profile_incomplete:
                # Check if they even have a password set
                if not user.password_hash:
                    # Always generate a new token and send email
                    token = user.generate_profile_completion_token()
                    db.session.commit()

                    # Send profile completion email
                    profile_completion_url = url_for('complete_profile', token=token, _external=True)
                    # Get the event they checked into
                    latest_checkin = EventCheckIn.query.filter_by(user_id=user.id, is_walk_in=True).order_by(EventCheckIn.checked_in_at.desc()).first()
                    event_title = latest_checkin.event.title if latest_checkin else "our event"
                    success, error = send_walk_in_welcome_email(mail, app.config['MAIL_DEFAULT_SENDER'], user, event_title, profile_completion_url)

                    email_sent = False
                    if success:
                        email_sent = True
                    else:
                        flash(f'Failed to send profile completion email: {error}', 'error')

                    # Render special page for incomplete profile
                    return render_template('profile_incomplete.html',
                                         user_email=user.email,
                                         has_password=False,
                                         email_sent=email_sent)

            # Normal login flow
            if user.check_password(password):
                login_user(user)
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                else:
                    # Check if user has already completed an assessment
                    existing_assessment = Assessment.query.filter_by(user_id=user.id).first()
                    if existing_assessment:
                        return redirect(url_for('user_dashboard'))
                    else:
                        return redirect(url_for('assessment'))

        flash('Invalid credentials.')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Forgot password route
@app.route('/forgot-password', methods=['GET', 'POST'])
@beta_access_required
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Please enter your email address.')
            return redirect(url_for('forgot_password'))

        user = User.query.filter_by(email=email).first()

        # Always show success message for security (don't reveal if email exists)
        flash('If an account exists with that email, you will receive a password reset link shortly.')

        if user:
            # Check if user has incomplete profile (walk-in user)
            if user.profile_incomplete:
                # Send profile completion email instead of password reset
                # Always generate a new token and send email
                token = user.generate_profile_completion_token()
                db.session.commit()

                # Send profile completion email
                profile_completion_url = url_for('complete_profile', token=token, _external=True)
                # Get the event they checked into
                latest_checkin = EventCheckIn.query.filter_by(user_id=user.id, is_walk_in=True).order_by(EventCheckIn.checked_in_at.desc()).first()
                event_title = latest_checkin.event.title if latest_checkin else "our event"
                send_walk_in_welcome_email(mail, app.config['MAIL_DEFAULT_SENDER'], user, event_title, profile_completion_url)
            else:
                # Generate reset token
                token = user.generate_reset_token()
                db.session.commit()

                # Send email
                reset_url = url_for('reset_password', token=token, _external=True)
                send_password_reset_email(mail, app.config['MAIL_DEFAULT_SENDER'], user, reset_url)
                # Note: Intentionally not checking return value for security reasons
                # (don't reveal whether email exists)

        return redirect(url_for('login'))

    return render_template('forgot_password.html')

# Reset password route
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
@beta_access_required
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset link. Please request a new password reset.')
        return redirect(url_for('forgot_password'))

    # Check if user has incomplete profile (walk-in user)
    # They should complete their profile first, not reset password
    if user.profile_incomplete:
        flash('Your account was created at an event but is incomplete. Please complete your profile using the link sent to your email.')
        return render_template('profile_incomplete.html',
                             user_email=user.email,
                             has_password=False,
                             email_sent=False)

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or not confirm_password:
            flash('Please fill in all fields.')
            return redirect(url_for('reset_password', token=token))

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password', token=token))

        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message)
            return redirect(url_for('reset_password', token=token))

        # Update password and clear reset token
        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()

        flash('Your password has been reset successfully! You can now log in with your new password.')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

# Email verification route
@app.route('/verify-email/<token>')
@beta_access_required
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if not user or not user.verify_email_token(token):
        flash('Invalid or expired verification link. Please request a new verification email.')
        if current_user.is_authenticated:
            return redirect(url_for('user_dashboard'))
        return redirect(url_for('login'))

    # Clear verification token
    user.clear_verification_token()
    db.session.commit()

    flash('Your email has been verified successfully! You now have full access to your matches.')
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

# Resend verification email route
@app.route('/resend-verification')
@login_required
@beta_access_required
def resend_verification():
    # Only allow unverified users to resend
    if current_user.email_verified:
        flash('Your email is already verified.')
        return redirect(url_for('user_dashboard'))

    # Rate limiting: Check if token was recently generated (within last 5 minutes)
    if current_user.verification_token_expiry:
        from datetime import datetime, timedelta
        time_since_last_token = datetime.utcnow() - (current_user.verification_token_expiry - timedelta(hours=24))
        if time_since_last_token < timedelta(minutes=5):
            remaining_seconds = int((timedelta(minutes=5) - time_since_last_token).total_seconds())
            flash(f'Please wait {remaining_seconds} seconds before requesting another verification email.')
            return redirect(url_for('user_dashboard'))

    # Generate new verification token
    token = current_user.generate_verification_token()
    db.session.commit()

    # Send verification email
    verification_url = url_for('verify_email', token=token, _external=True)
    send_verification_email(mail, app.config['MAIL_DEFAULT_SENDER'], current_user, verification_url)

    flash('Verification email sent! Please check your inbox.')
    return redirect(url_for('user_dashboard'))

# Verify email change route
@app.route('/verify-email-change/<token>')
@beta_access_required
def verify_email_change(token):
    user = User.query.filter_by(email_change_token=token).first()

    if not user or not user.verify_email_change_token(token):
        flash('Invalid or expired verification link. Please try changing your email again.')
        if current_user.is_authenticated:
            return redirect(url_for('user_dashboard'))
        return redirect(url_for('login'))

    # Check if the pending email is already taken by another user
    if user.pending_email:
        existing_user = User.query.filter_by(email=user.pending_email).first()
        if existing_user and existing_user.id != user.id:
            flash('This email address is already in use by another account.')
            user.clear_email_change_token()
            db.session.commit()
            return redirect(url_for('user_dashboard'))

        # Update the email address
        old_email = user.email
        user.email = user.pending_email
        user.email_verified = True  # Mark new email as verified
        user.clear_email_change_token()
        db.session.commit()

        flash(f'Your email has been successfully updated to {user.email}!')
    else:
        flash('Email change request not found.')
        user.clear_email_change_token()
        db.session.commit()

    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

# Assessment route
@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    # Check if user is logged in
    if not current_user.is_authenticated:
        flash('Please log in to access the assessment.')
        return redirect(url_for('login'))

    # Check if user can access the assessment
    if not current_user.can_access_assessment():
        flash('You have already completed your assessment. Please contact us if you would like to retake it!')
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        import json

        # Debug: Print all form data
        print("=== FORM DATA RECEIVED ===")
        for key, value in request.form.items():
            print(f"{key}: {value}")
        print("=========================")

        # Collect all assessment responses - store as flat dictionary with field names as keys
        # This matches the new assessment structure in assessment.html
        assessment_data = {}

        # Iterate through all form fields and store them with their exact field names
        for key in request.form.keys():
            # Handle multi-value fields (checkboxes, multi-select)
            values = request.form.getlist(key)
            if len(values) > 1:
                # Multiple values selected - sanitize each value
                assessment_data[key] = [sanitize_input(v, max_length=1000) for v in values]
            else:
                # Single value - sanitize
                assessment_data[key] = sanitize_input(request.form.get(key), max_length=1000)

        # Additional sanitization of the entire data structure
        assessment_data = sanitize_json_data(assessment_data)

        # Convert to JSON string for storage
        answers_json = json.dumps(assessment_data, indent=2)

        assessment = Assessment(user_id=current_user.id, answers=answers_json)
        db.session.add(assessment)
        db.session.commit()
        return redirect(url_for('assessment_thank_you'))
    return render_template('assessment.html')

# Assessment thank you page
@app.route('/assessment/thank-you')
@login_required
def assessment_thank_you():
    return render_template('assessment_thank_you.html')

# Disclaimer page - standalone page for agreeing to terms
@app.route('/disclaimer', methods=['GET', 'POST'])
@login_required
def disclaimer():
    # If already agreed, redirect to dashboard
    if current_user.disclaimer_agreed:
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        if request.form.get('agree_disclaimer'):
            # Mark user as having agreed to disclaimer
            current_user.disclaimer_agreed = True
            current_user.disclaimer_agreed_at = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('user_dashboard'))
        else:
            flash('You must agree to the terms to continue.')

    return render_template('disclaimer.html')

# API endpoint for agreeing to disclaimer from dashboard modal
@app.route('/api/agree_disclaimer', methods=['POST'])
@login_required
def api_agree_disclaimer():
    """API endpoint for users to agree to disclaimer from the dashboard modal"""
    current_user.disclaimer_agreed = True
    current_user.disclaimer_agreed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

# Admin dashboard route - main overview
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    # Get summary statistics
    total_assessments = Assessment.query.count()
    pending_assessments = Assessment.query.filter_by(reviewed=False).count()
    pending_matches = Match.query.filter_by(status='pending').count()
    completed_matches = Match.query.filter_by(status='finalized').count()
    total_users = User.query.filter_by(is_admin=False).count()

    return render_template('admin_main.html',
                         total_assessments=total_assessments,
                         pending_assessments=pending_assessments,
                         pending_matches=pending_matches,
                         completed_matches=completed_matches,
                         total_users=total_users)

# Admin users page - view all registered users
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    # Get filter parameter
    filter_type = request.args.get('filter', 'all')

    # Get all non-admin users
    users_query = User.query.filter_by(is_admin=False)

    # Apply filter
    if filter_type == 'has_assessment':
        # Get users who have completed an assessment
        user_ids_with_assessment = db.session.query(Assessment.user_id).distinct()
        users_query = users_query.filter(User.id.in_(user_ids_with_assessment))
    elif filter_type == 'no_assessment':
        # Get users who have NOT completed an assessment
        user_ids_with_assessment = db.session.query(Assessment.user_id).distinct()
        users_query = users_query.filter(~User.id.in_(user_ids_with_assessment))
    elif filter_type == 'not_paid':
        # Get users who have not paid
        users_query = users_query.filter(User.has_paid == False)

    # Order by ID (registration order)
    users = users_query.order_by(User.id.desc()).all()

    # For each user, check if they have an assessment
    user_data = []
    for user in users:
        assessment = Assessment.query.filter_by(user_id=user.id).first()
        user_data.append({
            'user': user,
            'has_assessment': assessment is not None,
            'assessment_reviewed': assessment.reviewed if assessment else None
        })

    return render_template('admin_users.html',
                         user_data=user_data,
                         filter_type=filter_type)

# Admin complete assessment on behalf of user
@app.route('/admin/complete_assessment/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_complete_assessment(user_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    # Get the user
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('admin_users'))

    # Check if user already has an assessment
    existing_assessment = Assessment.query.filter_by(user_id=user_id).first()
    if existing_assessment:
        flash(f'{user.first_name} {user.last_name} already has an assessment. Please view it from the admin users page.')
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        import json

        # Debug: Print all form data
        print("=== ADMIN ASSESSMENT FORM DATA RECEIVED ===")
        for key, value in request.form.items():
            print(f"{key}: {value}")
        print("=========================")

        # Collect all assessment responses - same logic as regular assessment
        assessment_data = {}

        # Iterate through all form fields and store them with their exact field names
        for key in request.form.keys():
            # Handle multi-value fields (checkboxes, multi-select)
            values = request.form.getlist(key)
            if len(values) > 1:
                # Multiple values selected - sanitize each value
                assessment_data[key] = [sanitize_input(v, max_length=1000) for v in values]
            else:
                # Single value - sanitize
                assessment_data[key] = sanitize_input(request.form.get(key), max_length=1000)

        # Additional sanitization of the entire data structure
        assessment_data = sanitize_json_data(assessment_data)

        # Convert to JSON string for storage
        answers_json = json.dumps(assessment_data, indent=2)

        # Create assessment for the specified user (not current_user)
        assessment = Assessment(user_id=user_id, answers=answers_json)
        db.session.add(assessment)
        db.session.commit()

        flash(f'Assessment completed successfully for {user.first_name} {user.last_name}!')
        return redirect(url_for('admin_users'))

    # GET request - show the assessment form
    return render_template('admin_complete_assessment.html', user=user)

# Admin assessments page
@app.route('/admin/assessments', methods=['GET', 'POST'])
@login_required
def admin_assessments():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        assessment_id = request.form['assessment_id']
        matched_user_id = request.form['matched_user_id']

        assessment = Assessment.query.get(assessment_id)
        if assessment:
            # Mark the assessment as reviewed if it wasn't already
            if not assessment.reviewed:
                assessment.reviewed = True

            # Find the matched user's assessment (can be reviewed or unreviewed for multi-matching)
            matched_user_assessment = Assessment.query.filter_by(user_id=matched_user_id).first()
            if matched_user_assessment:
                # Check if these two users are already matched (prevent duplicate matches)
                existing_match = Match.query.filter(
                    Match.status == 'finalized',
                    or_(
                        and_(Match.user1_id == assessment.user_id, Match.user2_id == matched_user_id),
                        and_(Match.user1_id == matched_user_id, Match.user2_id == assessment.user_id)
                    )
                ).first()

                if existing_match:
                    flash('These users are already matched. Please select a different user.')
                else:
                    # Mark as reviewed if it wasn't already
                    if not matched_user_assessment.reviewed:
                        matched_user_assessment.reviewed = True

                    # Create a new pending match
                    new_match = Match(
                        user1_id=assessment.user_id,
                        user2_id=matched_user_id,
                        assessment1_id=assessment.id,
                        assessment2_id=matched_user_assessment.id,
                        status='pending'
                    )
                    db.session.add(new_match)
                    db.session.commit()

                    flash('Pending match created successfully. Review it in the Pending Matches section.')
            else:
                flash('Matched user has no assessment.')

            return redirect(url_for('admin_assessments'))
        else:
            flash('Assessment not found.')

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Filter parameters
    filter_status = request.args.get('filter', 'all')
    search_query = request.args.get('search', '').strip()
    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    location_filter = request.args.get('location', '').strip()
    pronouns_filter = request.args.get('pronouns', '').strip()

    # Assessment answer filters
    emotional_availability_min = request.args.get('emotional_availability_min', type=int)
    recharge_style = request.args.get('recharge_style', '').strip()

    # Payment status filter (hidden from UI but kept for backward compat)
    payment_status_filter = request.args.getlist('payment_status')

    # RSVP event filter
    rsvp_event_filter = request.args.get('rsvp_event', type=int)

    # Build base query with join to User table
    query = Assessment.query.join(User, Assessment.user_id == User.id)

    # Apply review status filter
    if filter_status == 'reviewed':
        query = query.filter(Assessment.reviewed == True)
    elif filter_status == 'unreviewed':
        query = query.filter(Assessment.reviewed == False)
    # 'all' means no filter on reviewed status

    # Apply user criteria filters
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )

    if age_min or age_max:
        from datetime import date
        today = date.today()

        if age_min:
            # Calculate the latest birth date for minimum age
            max_birth_date = date(today.year - age_min, today.month, today.day)
            query = query.filter(User.date_of_birth <= max_birth_date)

        if age_max:
            # Calculate the earliest birth date for maximum age
            min_birth_date = date(today.year - age_max - 1, today.month, today.day)
            query = query.filter(User.date_of_birth >= min_birth_date)

    if location_filter:
        query = query.filter(User.location.ilike(f'%{location_filter}%'))

    if pronouns_filter:
        query = query.filter(User.pronouns.ilike(f'%{pronouns_filter}%'))

    # Apply payment status filter
    if 'paid' in payment_status_filter and 'not_paid' not in payment_status_filter:
        query = query.filter(User.has_paid == True)
    elif 'not_paid' in payment_status_filter and 'paid' not in payment_status_filter:
        query = query.filter(User.has_paid == False)
    # If both or neither selected, show all users

    # Apply RSVP event filter
    if rsvp_event_filter:
        rsvp_user_ids = [r.user_id for r in EventRSVP.query.filter_by(event_id=rsvp_event_filter).all()]
        query = query.filter(User.id.in_(rsvp_user_ids))

    # Get all assessments matching the filters (we'll filter by assessment answers in Python)
    all_matching_assessments = query.all()

    # Filter by assessment answers (since answers is JSON, we need to do this in Python)
    filtered_assessments = []
    for assessment in all_matching_assessments:
        if assessment.answers:
            try:
                assessment_data = json.loads(assessment.answers)

                # Apply emotional availability filter
                if emotional_availability_min is not None:
                    emotional_avail = assessment_data.get('friendship_readiness_emotional_availability')
                    if emotional_avail is None or int(emotional_avail) < emotional_availability_min:
                        continue

                # Apply recharge style filter
                if recharge_style:
                    recharge = assessment_data.get('personality_social_style_recharge_style')
                    if recharge != recharge_style:
                        continue

                filtered_assessments.append(assessment)
            except:
                # If JSON parsing fails, include the assessment
                filtered_assessments.append(assessment)
        else:
            filtered_assessments.append(assessment)

    # Manual pagination on filtered results
    total_items = len(filtered_assessments)
    total_pages = max(1, (total_items + per_page - 1) // per_page)  # Ceiling division, at least 1 page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    assessments = filtered_assessments[start_idx:end_idx]

    users = User.query.order_by(User.last_name, User.first_name).all()

    # Build user -> RSVPed event IDs mapping for match-with-user event filter
    user_rsvp_events = {}
    for rsvp in EventRSVP.query.all():
        user_rsvp_events.setdefault(rsvp.user_id, []).append(rsvp.event_id)

    # Count how many matches each user has by querying the Match table
    # Also track which users are matched with each assessment's user (to prevent duplicate matches)
    # And track which users were previously matched but are now unmatched (for warnings)
    user_match_counts = {}
    user_existing_matches = {}  # Maps user_id -> set of user_ids they're already matched with
    user_previous_matches = {}  # Maps user_id -> set of user_ids they were previously matched with but are now unmatched
    finalized_matches = Match.query.filter_by(status='finalized').all()
    unmatched_matches = Match.query.filter_by(status='unmatched').all()

    for match in finalized_matches:
        # Count matches for user1
        if match.user1_id not in user_match_counts:
            user_match_counts[match.user1_id] = 0
        user_match_counts[match.user1_id] += 1

        # Count matches for user2
        if match.user2_id not in user_match_counts:
            user_match_counts[match.user2_id] = 0
        user_match_counts[match.user2_id] += 1

        # Track existing match pairs (bidirectional)
        if match.user1_id not in user_existing_matches:
            user_existing_matches[match.user1_id] = set()
        user_existing_matches[match.user1_id].add(match.user2_id)

        if match.user2_id not in user_existing_matches:
            user_existing_matches[match.user2_id] = set()
        user_existing_matches[match.user2_id].add(match.user1_id)

    # Track previous matches that are now unmatched
    for match in unmatched_matches:
        if match.user1_id not in user_previous_matches:
            user_previous_matches[match.user1_id] = set()
        user_previous_matches[match.user1_id].add(match.user2_id)

        if match.user2_id not in user_previous_matches:
            user_previous_matches[match.user2_id] = set()
        user_previous_matches[match.user2_id].add(match.user1_id)

    # Process assessments for display
    assessments_with_scores = []
    for assessment in assessments:
        assessment_data = None
        scores = None
        overall_score = None
        insights = []

        if assessment.answers:
            try:
                assessment_data = json.loads(assessment.answers)
                # Only calculate scores if old format (has friendship_readiness)
                if 'friendship_readiness' in assessment_data:
                    scores, overall_score = calculate_friendship_scores(assessment_data)
                    insights = get_personalized_insights(assessment_data, scores)
            except:
                pass

        assessments_with_scores.append({
            'assessment': assessment,
            'assessment_data': assessment_data,
            'scores': scores,
            'overall_score': overall_score,
            'insights': insights
        })

    # Events for RSVP filter dropdown
    all_events = Event.query.order_by(Event.date_time.desc()).all()

    return render_template('admin_assessments.html',
                         assessments_with_scores=assessments_with_scores,
                         users=users,
                         user_match_counts=user_match_counts,
                         user_existing_matches=user_existing_matches,
                         user_previous_matches=user_previous_matches,
                         filter_status=filter_status,
                         page=page,
                         per_page=per_page,
                         total_pages=total_pages,
                         total_items=total_items,
                         search_query=search_query,
                         age_min=age_min,
                         age_max=age_max,
                         location_filter=location_filter,
                         pronouns_filter=pronouns_filter,
                         emotional_availability_min=emotional_availability_min,
                         recharge_style=recharge_style,
                         payment_status_filter=payment_status_filter,
                         all_events=all_events,
                         rsvp_event_filter=rsvp_event_filter,
                         user_rsvp_events=user_rsvp_events)

@app.route('/api/admin/matches/search')
@login_required
def api_admin_matches_search():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    q = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    finalized_matches = Match.query.filter_by(status='finalized').all()

    results = []
    for match in finalized_matches:
        u1 = User.query.get(match.user1_id)
        u2 = User.query.get(match.user2_id)
        if not u1 or not u2:
            continue
        if q:
            haystack = f'{u1.first_name} {u1.last_name} {u2.first_name} {u2.last_name}'.lower()
            if q not in haystack:
                continue
        results.append({
            'match_id': match.id,
            'user1_id': u1.id,
            'user2_id': u2.id,
            'user1_first': u1.first_name,
            'user1_last': u1.last_name,
            'user1_email': u1.email,
            'user1_bio': (u1.bio[:50] + '…') if u1.bio and len(u1.bio) > 50 else (u1.bio or ''),
            'user1_picture': url_for('static', filename=u1.profile_picture) if u1.profile_picture else None,
            'user2_first': u2.first_name,
            'user2_last': u2.last_name,
            'user2_email': u2.email,
            'user2_bio': (u2.bio[:50] + '…') if u2.bio and len(u2.bio) > 50 else (u2.bio or ''),
            'user2_picture': url_for('static', filename=u2.profile_picture) if u2.profile_picture else None,
            'finalized_at': match.finalized_at.strftime('%B %d, %Y') if match.finalized_at else 'N/A',
        })

    total = len(results)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return jsonify({
        'matches': results[start:start + per_page],
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'per_page': per_page,
    })


@app.route('/api/admin/assessments/search')
@login_required
def api_admin_assessments_search():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'assessments': [], 'total': 0})

    pattern = f'%{q}%'
    rows = db.session.query(Assessment, User).join(User, Assessment.user_id == User.id).filter(
        or_(
            User.first_name.ilike(pattern),
            User.last_name.ilike(pattern),
            User.email.ilike(pattern)
        )
    ).all()

    results = []
    for a, u in rows:
        results.append({
            'id': a.id,
            'user_id': u.id,
            'user_name': f'{u.first_name} {u.last_name}',
            'user_email': u.email,
            'user_age': calculate_age(u.date_of_birth) if u.date_of_birth else None,
            'user_location': u.location or '',
            'user_pronouns': u.pronouns or '',
            'user_picture': url_for('static', filename=u.profile_picture) if u.profile_picture else None,
            'reviewed': a.reviewed,
        })

    return jsonify({
        'assessments': results,
        'total': len(results),
        'q': q,
    })


# Admin matches page
@app.route('/admin/matches')
@login_required
def admin_matches():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('search', '').strip()

    # Get finalized matches from Match table
    finalized_matches = Match.query.filter_by(status='finalized').all()

    # Build match data with user information
    all_matches_data = []
    for match in finalized_matches:
        user1 = User.query.get(match.user1_id)
        user2 = User.query.get(match.user2_id)
        if user1 and user2:
            all_matches_data.append({
                'match': match,
                'user1': user1,
                'user2': user2
            })

    # Apply search filter
    if search_query:
        q = search_query.lower()
        all_matches_data = [
            d for d in all_matches_data
            if q in (d['user1'].first_name + ' ' + d['user1'].last_name).lower()
            or q in (d['user2'].first_name + ' ' + d['user2'].last_name).lower()
            or q in d['user1'].first_name.lower()
            or q in d['user1'].last_name.lower()
            or q in d['user2'].first_name.lower()
            or q in d['user2'].last_name.lower()
        ]

    total_items = len(all_matches_data)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    start_idx = (page - 1) * per_page
    matches_data = all_matches_data[start_idx:start_idx + per_page]

    return render_template('admin_matches.html',
                         matches_data=matches_data,
                         page=page,
                         per_page=per_page,
                         total_pages=total_pages,
                         total_items=total_items,
                         search_query=search_query)

# Admin unmatch endpoint
@app.route('/admin/unmatch/<int:match_id>', methods=['POST'])
@login_required
def admin_unmatch(match_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    if match.status != 'finalized':
        return jsonify({'error': 'Only finalized matches can be unmatched'}), 400

    # Change match status to 'unmatched' to keep history
    match.status = 'unmatched'

    # Get both assessments
    assessment1 = Assessment.query.get(match.assessment1_id)
    assessment2 = Assessment.query.get(match.assessment2_id)

    # Clear the matched_user_id fields (legacy field)
    if assessment1:
        assessment1.matched_user_id = None
    if assessment2:
        assessment2.matched_user_id = None

    # Check if each user has any other matches (pending OR finalized)
    # If not, set their assessment back to unreviewed
    user1_other_matches = Match.query.filter(
        or_(Match.status == 'finalized', Match.status == 'pending'),
        or_(Match.user1_id == match.user1_id, Match.user2_id == match.user1_id),
        Match.id != match_id
    ).first()

    user2_other_matches = Match.query.filter(
        or_(Match.status == 'finalized', Match.status == 'pending'),
        or_(Match.user1_id == match.user2_id, Match.user2_id == match.user2_id),
        Match.id != match_id
    ).first()

    # If user1 has no other matches (pending or finalized), mark their assessment as unreviewed
    if not user1_other_matches and assessment1:
        assessment1.reviewed = False

    # If user2 has no other matches (pending or finalized), mark their assessment as unreviewed
    if not user2_other_matches and assessment2:
        assessment2.reviewed = False

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Match successfully unmatched',
        'user1_assessment_unreviewed': not user1_other_matches,
        'user2_assessment_unreviewed': not user2_other_matches
    })

# Admin waive payment for user
@app.route('/admin/waive_payment/<int:user_id>', methods=['POST'])
@login_required
def admin_waive_payment(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Mark payment as waived
    user.has_paid = True
    user.payment_waived_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Payment waived for {user.first_name} {user.last_name}'
    })

# Admin pending matches page
@app.route('/admin/pending-matches', methods=['GET', 'POST'])
@login_required
def admin_pending_matches():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        match_id = request.form.get('match_id')
        action = request.form.get('action')

        match = Match.query.get(match_id)
        if not match:
            flash('Match not found.')
            return redirect(url_for('admin_pending_matches'))

        if action == 'update_notes':
            # Update admin notes
            match.admin_notes = sanitize_input(request.form.get('admin_notes', ''))
            db.session.commit()
            flash('Notes updated successfully.')

        elif action == 'update_draft':
            # Update draft email
            match.draft_email = sanitize_input(request.form.get('draft_email', ''))
            db.session.commit()
            flash('Draft email updated successfully.')

        elif action == 'cancel_match':
            # Cancel the pending match and return assessments to review
            if match.status != 'pending':
                flash('Only pending matches can be cancelled.', 'error')
                return redirect(url_for('admin_pending_matches'))

            # Get both assessments
            assessment1 = Assessment.query.get(match.assessment1_id)
            assessment2 = Assessment.query.get(match.assessment2_id)

            # Clear the matched_user_id fields
            if assessment1:
                assessment1.matched_user_id = None
            if assessment2:
                assessment2.matched_user_id = None

            # Check if each user has any other matches (pending OR finalized)
            # Only return to unreviewed if they have NO other matches
            user1_other_matches = Match.query.filter(
                or_(Match.status == 'finalized', Match.status == 'pending'),
                or_(Match.user1_id == match.user1_id, Match.user2_id == match.user1_id),
                Match.id != match.id
            ).first()

            user2_other_matches = Match.query.filter(
                or_(Match.status == 'finalized', Match.status == 'pending'),
                or_(Match.user1_id == match.user2_id, Match.user2_id == match.user2_id),
                Match.id != match.id
            ).first()

            # If user1 has no other matches (pending or finalized), mark their assessment as unreviewed
            if not user1_other_matches and assessment1:
                assessment1.reviewed = False

            # If user2 has no other matches (pending or finalized), mark their assessment as unreviewed
            if not user2_other_matches and assessment2:
                assessment2.reviewed = False

            # Delete the pending match (no need to keep history for unfinalized matches)
            db.session.delete(match)
            db.session.commit()

            flash('Pending match cancelled successfully. Assessments returned to unreviewed if user has no other matches.', 'success')

        elif action == 'finalize_no_email':
            # Finalize the match WITHOUT sending emails
            match.status = 'finalized'
            match.finalized_at = datetime.utcnow()

            # Update the assessment records to reflect the match
            assessment1 = Assessment.query.get(match.assessment1_id)
            assessment2 = Assessment.query.get(match.assessment2_id)
            if assessment1:
                assessment1.matched_user_id = match.user2_id
            if assessment2:
                assessment2.matched_user_id = match.user1_id

            # Explicitly leave email content NULL (per user preference)
            match.user1_email_content = None
            match.user2_email_content = None

            # Commit to database
            db.session.commit()

            flash('Match finalized successfully WITHOUT sending emails. Users can now see the match on their dashboards.', 'success')

        elif action == 'finalize':
            # Save any draft email changes from the form before finalizing
            draft_email_from_form = sanitize_input(request.form.get('draft_email', ''))
            if draft_email_from_form:
                match.draft_email = draft_email_from_form

            # Finalize the match
            match.status = 'finalized'
            match.finalized_at = datetime.utcnow()

            # Update the assessment records to reflect the match
            assessment1 = Assessment.query.get(match.assessment1_id)
            assessment2 = Assessment.query.get(match.assessment2_id)
            if assessment1:
                assessment1.matched_user_id = match.user2_id
            if assessment2:
                assessment2.matched_user_id = match.user1_id

            # Send the drafted email to both users (SEND FIRST, then store)
            user1 = User.query.get(match.user1_id)
            user2 = User.query.get(match.user2_id)
            dashboard_url = url_for('user_dashboard', _external=True)

            # Track email sending success
            email_errors = []
            emails_sent = 0
            logo_url = url_for('static', filename='logo/three-of-cups-logo-new.png', _external=True)

            # Use the drafted email if available, otherwise use default template
            if match.draft_email:
                # Send one email to both users
                try:
                    from flask_mail import Message as MailMessage
                    # Replace placeholders in draft email
                    email_content = match.draft_email.replace('{user1_name}', user1.first_name)
                    email_content = email_content.replace('{user2_name}', user2.first_name)
                    email_content = email_content.replace('{user1_pronouns}', user1.pronouns or '')
                    email_content = email_content.replace('{user2_pronouns}', user2.pronouns or '')
                    email_content = email_content.replace('{dashboard_url}', dashboard_url)
                    email_content = sanitize_email_content(email_content)

                    msg = MailMessage(
                        f'Your Three of Cups Match: {user1.first_name} and {user2.first_name}!',
                        sender=app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[user1.email, user2.email]
                    )
                    msg.body = email_content
                    bold_words = [user1.first_name, user2.first_name, user1.pronouns or '', user2.pronouns or '']
                    msg.html = format_draft_email_to_html(email_content, bold_words=bold_words, logo_url=logo_url)
                    msg.charset = 'utf-8'
                    mail.send(msg)
                    emails_sent += 1
                    match.user1_email_content = email_content
                    match.user2_email_content = email_content
                except Exception as e:
                    error_msg = f"Failed to send email to {user1.email}, {user2.email}: {str(e)}"
                    print(error_msg)
                    app.logger.error(error_msg)
                    email_errors.append(error_msg)
            else:
                # Use default template — one email to both users
                if user1 and user2:
                    try:
                        success, text_content = send_match_notification_email(mail, app.config['MAIL_DEFAULT_SENDER'], user1, user2, dashboard_url, logo_url=logo_url)
                        if success and text_content:
                            match.user1_email_content = text_content
                            match.user2_email_content = text_content
                            emails_sent += 1
                        else:
                            email_errors.append(f"Failed to send default email to {user1.email}, {user2.email}")
                    except Exception as e:
                        error_msg = f"Error sending email to {user1.email}, {user2.email}: {str(e)}"
                        print(error_msg)
                        app.logger.error(error_msg)
                        email_errors.append(error_msg)

            # Commit to database after emails are sent
            db.session.commit()

            # Show appropriate flash message
            if email_errors:
                flash(f'Match finalized. Email errors: {"; ".join(email_errors)}', 'warning')
            else:
                flash('Match finalized successfully! Email sent to both users.', 'success')

        return redirect(url_for('admin_pending_matches'))

    # Get all pending matches
    pending_matches = Match.query.filter_by(status='pending').all()

    # Build match data with user and assessment information
    matches_data = []
    for match in pending_matches:
        user1 = User.query.get(match.user1_id)
        user2 = User.query.get(match.user2_id)
        assessment1 = Assessment.query.get(match.assessment1_id)
        assessment2 = Assessment.query.get(match.assessment2_id)

        # Parse assessment answers from JSON
        assessment1_answers = {}
        assessment2_answers = {}
        try:
            if assessment1 and assessment1.answers:
                assessment1_answers = json.loads(assessment1.answers)
        except:
            pass
        try:
            if assessment2 and assessment2.answers:
                assessment2_answers = json.loads(assessment2.answers)
        except:
            pass

        matches_data.append({
            'match': match,
            'user1': user1,
            'user2': user2,
            'assessment1': assessment1,
            'assessment2': assessment2,
            'assessment1_answers': assessment1_answers,
            'assessment2_answers': assessment2_answers
        })

    return render_template('admin_pending_matches.html', matches_data=matches_data)

# Admin reviewer assessments page
@app.route('/admin/reviewer-assessments', methods=['GET', 'POST'])
@login_required
def admin_reviewer_assessments():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        assessment_id = request.form.get('assessment_id')
        admin_notes = sanitize_input(request.form.get('admin_notes', ''), max_length=5000)
        reviewed = request.form.get('reviewed') == '1'

        assessment = ReviewerAssessment.query.get(assessment_id)
        if assessment:
            assessment.admin_notes = admin_notes
            assessment.reviewed = reviewed
            db.session.commit()
            flash('Reviewer assessment updated successfully.')
        else:
            flash('Assessment not found.')

        return redirect(url_for('admin_reviewer_assessments'))

    reviewer_assessments = ReviewerAssessment.query.order_by(ReviewerAssessment.created_at.desc()).all()

    # Process assessments for display
    assessments_with_data = []
    for assessment in reviewer_assessments:
        assessment_data = None
        if assessment.answers:
            try:
                assessment_data = json.loads(assessment.answers)
            except:
                pass

        assessments_with_data.append({
            'assessment': assessment,
            'assessment_data': assessment_data
        })

    return render_template('admin_reviewer_assessments.html',
                         assessments_with_data=assessments_with_data)

@app.route('/account-settings', methods=['GET', 'POST'])
@login_required
@beta_access_required
def account_settings():
    if request.method == 'POST':
        if 'first_name' in request.form:
            first_name = sanitize_input(request.form.get('first_name', ''), max_length=100, allow_newlines=False)
            if first_name:
                current_user.first_name = first_name
            else:
                flash('First name is required.')
                return redirect(url_for('account_settings'))

        if 'last_name' in request.form:
            last_name = sanitize_input(request.form.get('last_name', ''), max_length=100, allow_newlines=False)
            if last_name:
                current_user.last_name = last_name
            else:
                flash('Last name is required.')
                return redirect(url_for('account_settings'))

        if 'email' in request.form:
            email = sanitize_email(request.form.get('email', ''))
            if email:
                # Check if email is different from current email
                if email != current_user.email:
                    # Check if email is already used by another user
                    existing_user = User.query.filter_by(email=email).first()
                    if existing_user and existing_user.id != current_user.id:
                        flash('Email already exists.')
                        return redirect(url_for('account_settings'))

                    # Store old email for notification
                    old_email = current_user.email

                    # Store the new email as pending
                    current_user.pending_email = email

                    # Generate email change token
                    token = current_user.generate_email_change_token()
                    db.session.commit()

                    # Send notification to old email
                    send_email_change_notification(
                        mail,
                        app.config['MAIL_DEFAULT_SENDER'],
                        old_email,
                        current_user.first_name,
                        email
                    )

                    # Send verification email to new email
                    verification_url = url_for('verify_email_change', token=token, _external=True)
                    send_email_change_verification(
                        mail,
                        app.config['MAIL_DEFAULT_SENDER'],
                        email,
                        current_user.first_name,
                        verification_url,
                        old_email
                    )

                    flash(f'A verification email has been sent to {email}. Please check your inbox to complete the email change. Your current email will remain {old_email} until verified.')
                    return redirect(url_for('account_settings'))
            else:
                flash('Email is required.')
                return redirect(url_for('account_settings'))

        if 'username' in request.form:
            username = sanitize_username(request.form.get('username', ''))
            if username:
                # Check if username is already used by another user
                existing_user = User.query.filter_by(username=username).first()
                if existing_user and existing_user.id != current_user.id:
                    flash('Username already exists.')
                    return redirect(url_for('account_settings'))
                current_user.username = username
            else:
                flash('Username is required.')
                return redirect(url_for('account_settings'))

        if 'pronouns' in request.form:
            current_user.pronouns = sanitize_input(request.form.get('pronouns', ''), max_length=100, allow_newlines=False)

        if 'location' in request.form:
            current_user.location = sanitize_location(request.form.get('location', ''))

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                # Validate file upload
                is_valid, error_msg = validate_file_upload(file.filename)
                if not is_valid:
                    flash(error_msg)
                    return redirect(url_for('account_settings'))

                filename = secure_filename(file.filename)
                unique_filename = f"{current_user.id}_{filename}"

                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                current_user.profile_picture = f'uploads/{unique_filename}'

        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('account_settings'))

    return render_template('account_settings.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))

    matched_users = []
    user_assessment = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.id.desc()).first()

    results_data = None
    if user_assessment and user_assessment.answers:
        try:
            assessment_data = json.loads(user_assessment.answers)
            scores, overall_score = calculate_friendship_scores(assessment_data)
            insights = get_personalized_insights(assessment_data, scores)
            comparative_data = get_comparative_data()

            results_data = {
                'overall_score': overall_score,
                'scores': scores,
                'insights': insights,
                'comparative_data': comparative_data
            }
        except Exception as e:
            print(f"Error processing assessment: {e}")
            results_data = None

    # Initialize event lists
    upcoming_rsvp_events = []
    past_rsvp_events = []

    # Only show matches if email is verified (or if user is admin)
    if current_user.email_verified or current_user.is_admin:
        # Find finalized matches where current user is either user1 or user2
        from sqlalchemy import or_
        finalized_matches = Match.query.filter(
            Match.status == 'finalized',
            or_(Match.user1_id == current_user.id, Match.user2_id == current_user.id)
        ).all()

        for match in finalized_matches:
            # Get the other user in the match
            other_user_id = match.user2_id if match.user1_id == current_user.id else match.user1_id
            matched_user = User.query.get(other_user_id)
            if matched_user:
                # Check if this user is already in the list (avoid duplicates)
                if not any(m['user'].id == matched_user.id for m in matched_users):
                    # Determine if email content exists for THIS user
                    has_email = False
                    if current_user.id == match.user1_id:
                        has_email = match.user1_email_content is not None and match.user1_email_content.strip() != ''
                    else:
                        has_email = match.user2_email_content is not None and match.user2_email_content.strip() != ''

                    matched_users.append({
                        'user': matched_user,
                        'match_id': match.id,
                        'has_email_content': has_email
                    })

        # Get user's RSVP'd events
        user_rsvps = EventRSVP.query.filter_by(user_id=current_user.id).all()
        rsvp_event_ids = [rsvp.event_id for rsvp in user_rsvps]

        # Events are considered past 1 hour after their start time
        # Production server runs in UTC, but events are stored in EST
        # Convert UTC to EST by subtracting 5 hours, then subtract 1 hour buffer
        cutoff_time = datetime.now() - timedelta(hours=6)

        # Get upcoming events user has RSVP'd to
        upcoming_rsvp_events = Event.query.filter(
            Event.id.in_(rsvp_event_ids),
            Event.date_time >= cutoff_time
        ).order_by(Event.date_time.asc()).all() if rsvp_event_ids else []

        # Get past events user has RSVP'd to
        past_rsvp_events = Event.query.filter(
            Event.id.in_(rsvp_event_ids),
            Event.date_time < cutoff_time
        ).order_by(Event.date_time.desc()).all() if rsvp_event_ids else []

    # Show disclaimer modal if user has completed assessment but hasn't agreed to disclaimer
    show_disclaimer_modal = user_assessment is not None and not current_user.disclaimer_agreed

    return render_template('user_dashboard.html',
                         matched_users=matched_users,
                         results_data=results_data,
                         email_verified=current_user.email_verified,
                         upcoming_rsvp_events=upcoming_rsvp_events,
                         past_rsvp_events=past_rsvp_events,
                         show_disclaimer_modal=show_disclaimer_modal)

# API endpoint for viewing match email content in modal
@app.route('/api/match_email/<int:match_id>')
@login_required
def get_match_email(match_id):
    """
    API endpoint to fetch the personalized email content for a match.
    Returns the email content that was sent to the current user about this match.
    """
    # Fetch the match
    match = Match.query.get(match_id)

    if not match:
        return jsonify({'success': False, 'error': 'Match not found'}), 404

    # Verify the current user is part of this match (security check)
    if current_user.id != match.user1_id and current_user.id != match.user2_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    # Get the appropriate email content for this user
    if current_user.id == match.user1_id:
        email_content = match.user1_email_content
        # Get the match partner's name
        match_partner = User.query.get(match.user2_id)
    else:
        email_content = match.user2_email_content
        # Get the match partner's name
        match_partner = User.query.get(match.user1_id)

    # Handle edge case: older matches without stored email content
    if not email_content:
        return jsonify({
            'success': True,
            'email_content': None,
            'match_name': match_partner.first_name if match_partner else 'your match',
            'finalized_at': match.finalized_at.isoformat() if match.finalized_at else None,
            'message': 'Email content not available for this match'
        })

    # Return the email content
    return jsonify({
        'success': True,
        'email_content': email_content,
        'match_name': match_partner.first_name if match_partner else 'your match',
        'finalized_at': match.finalized_at.isoformat() if match.finalized_at else None
    })

# Admin API: Get all matches for a user
@app.route('/api/admin/user_matches/<int:user_id>')
@login_required
def admin_get_user_matches(user_id):
    """Get all finalized matches for a specific user (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    from sqlalchemy import or_
    matches = Match.query.filter(
        Match.status == 'finalized',
        or_(Match.user1_id == user_id, Match.user2_id == user_id)
    ).all()

    matches_data = []
    for match in matches:
        user1 = User.query.get(match.user1_id)
        user2 = User.query.get(match.user2_id)

        matches_data.append({
            'id': match.id,
            'user1_id': match.user1_id,
            'user2_id': match.user2_id,
            'user1': {
                'first_name': user1.first_name,
                'last_name': user1.last_name,
                'email': user1.email
            },
            'user2': {
                'first_name': user2.first_name,
                'last_name': user2.last_name,
                'email': user2.email
            },
            'user1_email_content': match.user1_email_content,
            'user2_email_content': match.user2_email_content,
            'finalized_at': match.finalized_at.isoformat() if match.finalized_at else None
        })

    return jsonify({'success': True, 'user_id': user_id, 'matches': matches_data})

# Admin API: Get email content for one user in a match
@app.route('/api/admin/match_email_content/<int:match_id>/<user_position>')
@login_required
def admin_get_match_email_content(match_id, user_position):
    """Get email content for a specific user in a match (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    if user_position not in ['user1', 'user2']:
        return jsonify({'error': 'Invalid user position. Must be user1 or user2'}), 400

    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    email_content = match.user1_email_content if user_position == 'user1' else match.user2_email_content

    return jsonify({
        'success': True,
        'email_content': email_content,
        'has_content': email_content is not None and email_content.strip() != ''
    })

# Admin API: Update email content for one user in a match
@app.route('/api/admin/update_match_email', methods=['POST'])
@login_required
def admin_update_match_email():
    """Update email content for a specific user in a match (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    match_id = data.get('match_id')
    user_position = data.get('user_position')
    email_content = data.get('email_content', '')

    if not match_id or not user_position:
        return jsonify({'error': 'Missing required fields'}), 400

    if user_position not in ['user1', 'user2']:
        return jsonify({'error': 'Invalid user position'}), 400

    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    # Sanitize input
    email_content = sanitize_input(email_content)

    # Update the appropriate field
    if user_position == 'user1':
        match.user1_email_content = email_content if email_content.strip() else None
    else:
        match.user2_email_content = email_content if email_content.strip() else None

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Email content updated successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating match email: {str(e)}")
        return jsonify({'error': 'Failed to update email content'}), 500

# Admin API: Update email content for BOTH users in a match
@app.route('/api/admin/update_match_emails_both', methods=['POST'])
@login_required
def admin_update_match_emails_both():
    """Update email content for both users in a match (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    match_id = data.get('match_id')
    user1_email_content = data.get('user1_email_content', '')
    user2_email_content = data.get('user2_email_content', '')

    if not match_id:
        return jsonify({'error': 'Missing match_id'}), 400

    match = Match.query.get(match_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    # Sanitize inputs
    user1_email_content = sanitize_input(user1_email_content)
    user2_email_content = sanitize_input(user2_email_content)

    # Update both fields
    match.user1_email_content = user1_email_content if user1_email_content.strip() else None
    match.user2_email_content = user2_email_content if user2_email_content.strip() else None

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Email contents updated successfully for both users'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating match emails: {str(e)}")
        return jsonify({'error': 'Failed to update email contents'}), 500

@app.route('/submit-feedback', methods=['POST'])
@login_required
@beta_access_required
def submit_feedback():
    feedback_type = request.form.get('feedback_type', 'general')
    feedback_subject = sanitize_input(request.form.get('feedback_subject', ''), max_length=200, allow_newlines=False)
    feedback_message = sanitize_input(request.form.get('feedback_message', ''), max_length=5000, allow_newlines=True)

    if not feedback_subject or not feedback_message:
        flash('Please provide both a subject and message for your feedback.')
        return redirect(url_for('user_dashboard'))

    # Map feedback type to readable label
    feedback_type_labels = {
        'event_recommendation': 'Event Recommendation',
        'app_issue': 'App Issue/Bug Report',
        'feature_request': 'Feature Request',
        'match_feedback': 'Feedback on Matches',
        'general': 'General Feedback',
        'other': 'Other'
    }
    feedback_type_label = feedback_type_labels.get(feedback_type, 'General Feedback')

    # Send feedback email to admin
    try:
        from flask_mail import Message
        msg = Message(
            subject=f'User Feedback: {feedback_type_label} - {feedback_subject}',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['admin@threeofcupsllc.com']
        )

        msg.body = f"""
User Feedback Submission

From: {current_user.first_name} {current_user.last_name} ({current_user.email})
User ID: {current_user.id}
Category: {feedback_type_label}
Subject: {feedback_subject}

Message:
{feedback_message}

---
Submitted on: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
        """

        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #C17767, #7A9B8E); padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="color: white; margin: 0;">User Feedback Submission</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #C17767; margin-top: 0;">Feedback Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">From:</td>
                            <td style="padding: 8px 0;">{current_user.first_name} {current_user.last_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Email:</td>
                            <td style="padding: 8px 0;">{current_user.email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">User ID:</td>
                            <td style="padding: 8px 0;">{current_user.id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Category:</td>
                            <td style="padding: 8px 0;"><span style="background-color: #C17767; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">{feedback_type_label}</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Subject:</td>
                            <td style="padding: 8px 0;">{feedback_subject}</td>
                        </tr>
                    </table>
                </div>

                <div style="background-color: white; padding: 20px; border-radius: 8px;">
                    <h4 style="color: #7A9B8E; margin-top: 0;">Message:</h4>
                    <p style="line-height: 1.6; color: #333; white-space: pre-wrap;">{feedback_message}</p>
                </div>

                <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
                    Submitted on {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
                </p>
            </div>
        </div>
        """

        mail.send(msg)
        flash('Thank you for your feedback! We appreciate you helping us improve Three of Cups.')
    except Exception as e:
        print(f"Error sending feedback email: {e}")
        flash('There was an issue submitting your feedback. Please try again or contact us directly at admin@threeofcupsllc.com')

    return redirect(url_for('user_dashboard'))

@app.route('/submit-event-recommendation', methods=['POST'])
@login_required
@beta_access_required
def submit_event_recommendation():
    event_type = request.form.get('event_type', '')
    event_title = sanitize_input(request.form.get('event_title', ''), max_length=200, allow_newlines=False)
    event_description = sanitize_input(request.form.get('event_description', ''), max_length=2000, allow_newlines=True)

    if not event_type or not event_title or not event_description:
        flash('Please fill out all fields for your event recommendation.')
        return redirect(url_for('events'))

    # Map event type to readable label
    event_type_labels = {
        'social': 'Social Gathering',
        'workshop': 'Workshop or Class',
        'wellness': 'Wellness Activity',
        'outdoor': 'Outdoor Adventure',
        'cultural': 'Cultural Experience',
        'creative': 'Creative Activity',
        'other': 'Other'
    }
    event_type_label = event_type_labels.get(event_type, 'Other')

    # Send event recommendation email to admin
    try:
        from flask_mail import Message
        msg = Message(
            subject=f'Event Recommendation: {event_type_label} - {event_title}',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['admin@threeofcupsllc.com']
        )

        msg.body = f"""
Event Recommendation Submission

From: {current_user.first_name} {current_user.last_name} ({current_user.email})
User ID: {current_user.id}
Event Type: {event_type_label}
Event Idea: {event_title}

Description:
{event_description}

---
Submitted on: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
        """

        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #9333ea, #ec4899); padding: 20px; border-radius: 8px 8px 0 0;">
                <h2 style="color: white; margin: 0;">Event Recommendation</h2>
            </div>
            <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
                <div style="background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #9333ea; margin-top: 0;">Recommendation Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">From:</td>
                            <td style="padding: 8px 0;">{current_user.first_name} {current_user.last_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Email:</td>
                            <td style="padding: 8px 0;">{current_user.email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">User ID:</td>
                            <td style="padding: 8px 0;">{current_user.id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Event Type:</td>
                            <td style="padding: 8px 0;"><span style="background-color: #9333ea; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">{event_type_label}</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Event Idea:</td>
                            <td style="padding: 8px 0;">{event_title}</td>
                        </tr>
                    </table>
                </div>

                <div style="background-color: white; padding: 20px; border-radius: 8px;">
                    <h4 style="color: #ec4899; margin-top: 0;">Description:</h4>
                    <p style="line-height: 1.6; color: #333; white-space: pre-wrap;">{event_description}</p>
                </div>

                <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
                    Submitted on {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
                </p>
            </div>
        </div>
        """

        mail.send(msg)
        flash('Thank you for your event recommendation! We love hearing ideas from our community.')
    except Exception as e:
        print(f"Error sending event recommendation email: {e}")
        flash('There was an issue submitting your recommendation. Please try again or contact us directly at admin@threeofcupsllc.com')

    return redirect(url_for('events'))

# Reviewer access routes
@app.route('/reviewer-login', methods=['GET', 'POST'])
def reviewer_login():
    if request.method == 'POST':
        access_code = request.form.get('access_code')
        if access_code == REVIEWER_ACCESS_CODE:
            session['reviewer_access'] = True
            return redirect(url_for('reviewer_assessment'))
        else:
            flash('Invalid access code.')
            return redirect(url_for('reviewer_login'))
    return render_template('reviewer_login.html')

@app.route('/reviewer-assessment', methods=['GET', 'POST'])
@reviewer_access_required
def reviewer_assessment():
    if request.method == 'POST':
        import json

        # Get basic information (with basics_ prefix as submitted by form) - sanitized
        name = sanitize_input(request.form.get('basics_name', ''), max_length=200, allow_newlines=False)
        pronouns = sanitize_input(request.form.get('basics_pronouns', ''), max_length=100, allow_newlines=False)
        age_range = sanitize_input(request.form.get('basics_age_range', ''), max_length=50, allow_newlines=False)
        location = sanitize_location(request.form.get('basics_location', ''))

        # Collect all assessment responses
        assessment_data = {}

        # Iterate through all form fields and store them with sanitization
        for key in request.form.keys():
            values = request.form.getlist(key)
            if len(values) > 1:
                assessment_data[key] = [sanitize_input(v, max_length=1000) for v in values]
            else:
                assessment_data[key] = sanitize_input(request.form.get(key), max_length=1000)

        # Additional sanitization of the entire data structure
        assessment_data = sanitize_json_data(assessment_data)

        # Convert to JSON string for storage
        answers_json = json.dumps(assessment_data, indent=2)

        # Create reviewer assessment record
        reviewer_assessment = ReviewerAssessment(
            name=name,
            pronouns=pronouns,
            age_range=age_range,
            location=location,
            answers=answers_json
        )
        db.session.add(reviewer_assessment)
        db.session.commit()

        return redirect(url_for('reviewer_thank_you'))

    return render_template('reviewer_assessment.html')

@app.route('/reviewer-assessment/thank-you')
@reviewer_access_required
def reviewer_thank_you():
    return render_template('reviewer_thank_you.html')

@app.route('/api/user_assessment/<int:user_id>')
@login_required
def get_user_assessment(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    assessment = Assessment.query.filter_by(user_id=user_id).first()
    if not assessment:
        return jsonify({'error': 'No assessment found'}), 404

    import json
    parsed_answers = {}

    if assessment.answers:
        try:
            # Try to parse as JSON (new format)
            assessment_data = json.loads(assessment.answers)
            parsed_answers = assessment_data
        except json.JSONDecodeError:
            # Fall back to old text format parsing
            questions = [
                "What are your main hobbies and interests?",
                "How do you prefer to spend your free time?",
                "What values are most important to you in friendships?",
                "What kind of social activities do you enjoy?",
                "How do you handle conflicts or disagreements?",
                "What gender(s) are you open to being matched with for friendship?"
            ]

            answer_blocks = assessment.answers.split('\n\n')
            for block in answer_blocks:
                if 'Q' in block and 'A:' in block:
                    lines = block.split('\n')
                    question_line = lines[0]
                    answer_line = '\n'.join(lines[1:]) if len(lines) > 1 else ''

                    # Extract question number
                    if question_line.startswith('Q') and ':' in question_line:
                        q_num = question_line.split(':')[0].replace('Q', '')
                        if q_num.isdigit():
                            q_index = int(q_num) - 1
                            if 0 <= q_index < len(questions):
                                parsed_answers[f'q{q_num}'] = {
                                    'question': questions[q_index],
                                    'answer': answer_line.replace('A: ', '', 1) if answer_line.startswith('A: ') else answer_line
                                }

    return jsonify({
        'user': {
            'id': user.id,
            'name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'bio': user.bio or 'No bio available',
            'profile_picture': user.profile_picture,
            'age': calculate_age(user.date_of_birth) if user.date_of_birth else None
        },
        'assessment': parsed_answers
    })

# Events routes
@app.route('/events')
@beta_access_required
def events():
    # Get view type (upcoming or past)
    view = request.args.get('view', 'upcoming')

    # Events are considered past 1 hour after their start time
    # Production server runs in UTC, but events are stored in EST
    # Convert UTC to EST by subtracting 5 hours, then subtract 1 hour buffer
    cutoff_time = datetime.now() - timedelta(hours=6)

    if view == 'past':
        # Get past events (ended more than 1 hour ago)
        events_list = Event.query.filter(
            Event.date_time < cutoff_time
        ).order_by(Event.date_time.desc()).all()
    else:
        # Get upcoming events (not yet past the 1 hour mark)
        events_list = Event.query.filter(
            Event.date_time >= cutoff_time
        ).order_by(Event.date_time.asc()).all()

    # Get user's RSVPs if authenticated
    user_rsvps = set()
    if current_user.is_authenticated:
        rsvps = EventRSVP.query.filter_by(user_id=current_user.id).all()
        user_rsvps = {rsvp.event_id for rsvp in rsvps}

    # Get RSVP counts for each event
    event_rsvp_counts = {}
    for event in events_list:
        count = EventRSVP.query.filter_by(event_id=event.id).count()
        event_rsvp_counts[event.id] = count

    return render_template('events.html',
                         events=events_list,
                         user_rsvps=user_rsvps,
                         event_rsvp_counts=event_rsvp_counts,
                         current_view=view)

@app.route('/admin/events', methods=['GET', 'POST'])
@login_required
def admin_events():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Sanitize inputs
        title = sanitize_input(request.form.get('title', ''), max_length=200, allow_newlines=False)
        description = sanitize_input(request.form.get('description', ''), max_length=5000)
        location = sanitize_location(request.form.get('location', ''))  # venue name
        address = sanitize_input(request.form.get('address', ''), max_length=500, allow_newlines=False)
        date_time_str = request.form.get('date_time', '').strip()
        end_time_str = request.form.get('end_time', '').strip()
        price_str = request.form.get('price', '').strip()
        price_max_str = request.form.get('price_max', '').strip()

        # Validate required fields
        if not all([title, description, location, date_time_str]):
            flash('Title, description, venue name, and date/time are required.')
            return redirect(url_for('admin_events'))

        # Parse date/time
        try:
            event_date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format.')
            return redirect(url_for('admin_events'))

        # Parse end time (optional)
        end_time = None
        if end_time_str:
            try:
                end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid end time format.')
                return redirect(url_for('admin_events'))

        # Parse price / energy exchange (optional)
        price = None
        if price_str:
            try:
                price = float(price_str)
                if price < 0:
                    flash('Energy exchange amount cannot be negative.')
                    return redirect(url_for('admin_events'))
            except ValueError:
                flash('Invalid energy exchange format.')
                return redirect(url_for('admin_events'))

        price_max = None
        if price_max_str:
            try:
                price_max = float(price_max_str)
                if price_max < 0:
                    flash('Energy exchange max cannot be negative.')
                    return redirect(url_for('admin_events'))
                if price is not None and price_max < price:
                    flash('Energy exchange max must be greater than the minimum.')
                    return redirect(url_for('admin_events'))
            except ValueError:
                flash('Invalid energy exchange max format.')
                return redirect(url_for('admin_events'))

        # Parse max_capacity (optional)
        max_capacity = None
        max_capacity_str = request.form.get('max_capacity', '').strip()
        if max_capacity_str:
            try:
                max_capacity = int(max_capacity_str)
                if max_capacity < 1:
                    flash('Max capacity must be at least 1.')
                    return redirect(url_for('admin_events'))
            except ValueError:
                flash('Invalid max capacity format.')
                return redirect(url_for('admin_events'))

        # Handle picture upload
        picture = None
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename != '':
                is_valid, error_msg = validate_file_upload(file.filename)
                if not is_valid:
                    flash(error_msg)
                    return redirect(url_for('admin_events'))

                filename = secure_filename(file.filename)
                unique_filename = f"event_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"

                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                picture = f'uploads/{unique_filename}'

        # Create event
        new_event = Event(
            title=title,
            description=description,
            location=location,
            address=address if address else None,
            date_time=event_date_time,
            end_time=end_time,
            price=price,
            price_max=price_max,
            picture=picture,
            max_capacity=max_capacity,
            created_by=current_user.id
        )
        db.session.add(new_event)
        db.session.commit()

        flash('Event created successfully!')
        return redirect(url_for('admin_events'))

    # Get all events (past and future)
    all_events = Event.query.order_by(Event.date_time.desc()).all()

    # Get RSVP counts and check-in data for each event
    event_data = []
    for event in all_events:
        # RSVPs
        rsvps = EventRSVP.query.filter_by(event_id=event.id).all()
        rsvp_users = []
        for rsvp in rsvps:
            user = User.query.get(rsvp.user_id)
            if user:
                rsvp_users.append(user)

        # Check-ins
        check_ins = EventCheckIn.query.filter_by(event_id=event.id).order_by(EventCheckIn.checked_in_at.desc()).all()
        check_in_count = len(check_ins)
        check_in_with_rsvp_count = sum(1 for c in check_ins if c.had_rsvp)
        walk_in_count = sum(1 for c in check_ins if not c.had_rsvp)

        # Energy exchanges (persist even after RSVP cancellation)
        energy_exchanges_raw = EventEnergyExchange.query.filter_by(event_id=event.id).all()
        energy_exchange_data = []
        for ee in energy_exchanges_raw:
            ee_user = User.query.get(ee.user_id)
            if ee_user:
                energy_exchange_data.append({'exchange': ee, 'user': ee_user})

        event_data.append({
            'event': event,
            'rsvp_count': len(rsvps),
            'rsvp_users': rsvp_users,
            'rsvp_user_ids': {u.id for u in rsvp_users},
            'check_ins': check_ins,
            'check_in_count': check_in_count,
            'check_in_with_rsvp_count': check_in_with_rsvp_count,
            'walk_in_count': walk_in_count,
            'energy_exchanges': energy_exchange_data
        })

    # Events are considered past 1 hour after their start time
    # Production server runs in UTC, but events are stored in EST
    # Convert UTC to EST by subtracting 5 hours, then subtract 1 hour buffer
    cutoff_time = datetime.now() - timedelta(hours=6)
    all_users = User.query.filter_by(is_admin=False).order_by(User.last_name, User.first_name).all()
    return render_template('admin_events.html', event_data=event_data, now=cutoff_time, all_users=all_users)

@app.route('/api/event/rsvp/<int:event_id>', methods=['POST'])
@login_required
def rsvp_event(event_id):
    """Handle RSVP for free events. Paid events use /api/event/rsvp/confirm/<id>."""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # If event has a price, client should use the confirm endpoint (after modal)
    if event.price:
        return jsonify({'error': 'This event requires energy exchange confirmation', 'requires_payment': True}), 400

    # Check if user already RSVP'd
    existing_rsvp = EventRSVP.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()

    if existing_rsvp:
        return jsonify({'error': 'Already RSVP\'d to this event'}), 400

    # Check if event is at capacity
    if event.max_capacity:
        current_rsvp_count = EventRSVP.query.filter_by(event_id=event_id).count()
        if current_rsvp_count >= event.max_capacity:
            return jsonify({'error': 'This event is at capacity'}), 400

    # Create RSVP
    rsvp = EventRSVP(event_id=event_id, user_id=current_user.id)
    db.session.add(rsvp)
    db.session.commit()

    return jsonify({'success': True, 'message': 'RSVP successful!'})


@app.route('/api/event/rsvp/confirm/<int:event_id>', methods=['POST'])
@login_required
def rsvp_event_confirm(event_id):
    """Finalize RSVP for paid events after user confirms energy exchange was sent."""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # Check if user already RSVP'd
    existing_rsvp = EventRSVP.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()

    if existing_rsvp:
        return jsonify({'error': 'Already RSVP\'d to this event'}), 400

    # Check if event is at capacity
    if event.max_capacity:
        current_rsvp_count = EventRSVP.query.filter_by(event_id=event_id).count()
        if current_rsvp_count >= event.max_capacity:
            return jsonify({'error': 'This event is at capacity'}), 400

    # Create RSVP
    rsvp = EventRSVP(event_id=event_id, user_id=current_user.id)
    db.session.add(rsvp)

    # Record energy exchange indication (idempotent - only create if not already there)
    existing_ee = EventEnergyExchange.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()
    if not existing_ee:
        ee = EventEnergyExchange(event_id=event_id, user_id=current_user.id)
        db.session.add(ee)

    db.session.commit()

    # Build energy exchange display string for admin email
    if event.price and event.price_max:
        ee_amount = f'${event.price:.2f} - ${event.price_max:.2f}'
    elif event.price:
        ee_amount = f'${event.price:.2f}'
    else:
        ee_amount = None

    # Notify admin
    try:
        send_rsvp_admin_notification(
            mail,
            app.config['MAIL_DEFAULT_SENDER'],
            'admin@threeofcupsllc.com',
            current_user,
            event,
            energy_exchange_amount=ee_amount
        )
    except Exception as e:
        print(f"Admin RSVP notification error: {e}")

    return jsonify({'success': True, 'message': 'RSVP confirmed! We can\'t wait to see you!'})

@app.route('/api/event/unrsvp/<int:event_id>', methods=['POST'])
@login_required
def unrsvp_event(event_id):
    event = Event.query.get(event_id)
    rsvp = EventRSVP.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()

    if not rsvp:
        return jsonify({'error': 'RSVP not found'}), 404

    db.session.delete(rsvp)
    db.session.commit()

    # Notify admin of cancellation
    if event:
        try:
            send_rsvp_cancellation_admin_notification(
                mail,
                app.config['MAIL_DEFAULT_SENDER'],
                'admin@threeofcupsllc.com',
                current_user,
                event
            )
        except Exception as e:
            print(f"Admin cancellation notification error: {e}")

    return jsonify({'success': True, 'message': 'RSVP removed successfully!'})


@app.route('/api/admin/event/<int:event_id>/rsvp/add', methods=['POST'])
@login_required
def admin_add_rsvp(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    data = request.get_json()
    user_id = data.get('user_id') if data else None
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    existing = EventRSVP.query.filter_by(event_id=event_id, user_id=user_id).first()
    if existing:
        return jsonify({'error': f'{user.first_name} {user.last_name} is already RSVP\'d to this event'}), 400

    rsvp = EventRSVP(event_id=event_id, user_id=user_id)
    db.session.add(rsvp)
    db.session.commit()

    new_count = EventRSVP.query.filter_by(event_id=event_id).count()
    over_capacity = bool(event.max_capacity and new_count > event.max_capacity)
    return jsonify({
        'success': True,
        'message': f'{user.first_name} {user.last_name} added to RSVP list.',
        'over_capacity': over_capacity,
        'new_count': new_count
    })


@app.route('/api/admin/event/<int:event_id>/rsvp/remove', methods=['POST'])
@login_required
def admin_remove_rsvp(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    data = request.get_json()
    user_id = data.get('user_id') if data else None
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    rsvp = EventRSVP.query.filter_by(event_id=event_id, user_id=user_id).first()
    if not rsvp:
        return jsonify({'error': 'RSVP not found'}), 404

    db.session.delete(rsvp)
    db.session.commit()

    new_count = EventRSVP.query.filter_by(event_id=event_id).count()
    return jsonify({'success': True, 'message': 'RSVP removed.', 'new_count': new_count})


@app.route('/api/admin/event/<int:event_id>/energy-exchange/confirm', methods=['POST'])
@login_required
def confirm_energy_exchange(event_id):
    """Admin confirms an energy exchange payment for a specific user."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    notes = data.get('notes', '')

    ee = EventEnergyExchange.query.filter_by(event_id=event_id, user_id=user_id).first()
    if not ee:
        return jsonify({'error': 'Energy exchange record not found'}), 404

    ee.confirmed = True
    if amount is not None:
        try:
            ee.amount_confirmed = float(amount)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount'}), 400
    if notes:
        ee.admin_notes = notes[:500]

    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    event = Event.query.get(event_id)
    if not event:
        flash('Event not found.')
        return redirect(url_for('admin_events'))

    # Delete all RSVPs first
    EventRSVP.query.filter_by(event_id=event_id).delete()

    # Delete event
    db.session.delete(event)
    db.session.commit()

    flash('Event deleted successfully!')
    return redirect(url_for('admin_events'))

@app.route('/admin/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    event = Event.query.get(event_id)
    if not event:
        flash('Event not found.')
        return redirect(url_for('admin_events'))

    if request.method == 'POST':
        # Sanitize inputs
        title = sanitize_input(request.form.get('title', ''), max_length=200, allow_newlines=False)
        description = sanitize_input(request.form.get('description', ''), max_length=5000)
        location = sanitize_location(request.form.get('location', ''))  # venue name
        address = sanitize_input(request.form.get('address', ''), max_length=500, allow_newlines=False)
        date_time_str = request.form.get('date_time', '').strip()
        end_time_str = request.form.get('end_time', '').strip()
        price_str = request.form.get('price', '').strip()
        price_max_str = request.form.get('price_max', '').strip()

        # Validate required fields
        if not all([title, description, location, date_time_str]):
            flash('Title, description, venue name, and date/time are required.')
            return redirect(url_for('edit_event', event_id=event_id))

        # Parse date/time
        try:
            event_date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format.')
            return redirect(url_for('edit_event', event_id=event_id))

        # Parse end time (optional)
        end_time = None
        if end_time_str:
            try:
                end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid end time format.')
                return redirect(url_for('edit_event', event_id=event_id))

        # Parse price / energy exchange (optional)
        price = None
        if price_str:
            try:
                price = float(price_str)
                if price < 0:
                    flash('Energy exchange amount cannot be negative.')
                    return redirect(url_for('edit_event', event_id=event_id))
            except ValueError:
                flash('Invalid energy exchange format.')
                return redirect(url_for('edit_event', event_id=event_id))

        price_max = None
        if price_max_str:
            try:
                price_max = float(price_max_str)
                if price_max < 0:
                    flash('Energy exchange max cannot be negative.')
                    return redirect(url_for('edit_event', event_id=event_id))
                if price is not None and price_max < price:
                    flash('Energy exchange max must be greater than the minimum.')
                    return redirect(url_for('edit_event', event_id=event_id))
            except ValueError:
                flash('Invalid energy exchange max format.')
                return redirect(url_for('edit_event', event_id=event_id))

        # Parse max_capacity (optional)
        max_capacity = None
        max_capacity_str = request.form.get('max_capacity', '').strip()
        if max_capacity_str:
            try:
                max_capacity = int(max_capacity_str)
                if max_capacity < 1:
                    flash('Max capacity must be at least 1.')
                    return redirect(url_for('edit_event', event_id=event_id))

                # Check if new capacity is less than current RSVPs
                current_rsvp_count = EventRSVP.query.filter_by(event_id=event_id).count()
                if max_capacity < current_rsvp_count:
                    flash(f'Max capacity cannot be less than current RSVPs ({current_rsvp_count}).')
                    return redirect(url_for('edit_event', event_id=event_id))
            except ValueError:
                flash('Invalid max capacity format.')
                return redirect(url_for('edit_event', event_id=event_id))

        # Handle picture upload
        picture = event.picture  # Keep existing picture by default
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename != '':
                is_valid, error_msg = validate_file_upload(file.filename)
                if not is_valid:
                    flash(error_msg)
                    return redirect(url_for('edit_event', event_id=event_id))

                filename = secure_filename(file.filename)
                unique_filename = f"event_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"

                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)

                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                picture = f'uploads/{unique_filename}'

                # Delete old picture if it exists and is different
                if event.picture and event.picture != picture:
                    old_file_path = os.path.join('static', event.picture)
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except Exception:
                            pass  # Ignore errors when deleting old file

        # Update event
        event.title = title
        event.description = description
        event.location = location
        event.address = address if address else None
        event.date_time = event_date_time
        event.end_time = end_time
        event.price = price
        event.price_max = price_max
        event.picture = picture
        event.max_capacity = max_capacity

        db.session.commit()

        flash('Event updated successfully!')
        return redirect(url_for('admin_events'))

    # GET request - show edit form
    # Get RSVP count for capacity validation
    rsvp_count = EventRSVP.query.filter_by(event_id=event.id).count()

    return render_template('edit_event.html', event=event, rsvp_count=rsvp_count)

# Event Check-In System Routes

@app.route('/event/<int:event_id>/kiosk')
@beta_access_required
def event_kiosk(event_id):
    # Validate token
    token = request.args.get('token')
    event = Event.query.get(event_id)

    if not event:
        flash('Event not found.')
        return redirect(url_for('events'))

    if not token or event.kiosk_token != token:
        flash('Invalid or expired kiosk access link.')
        return redirect(url_for('events'))

    # Check if token expired
    if event.kiosk_token_expiry and datetime.utcnow() > event.kiosk_token_expiry:
        flash('This kiosk link has expired.')
        return redirect(url_for('events'))

    return render_template('event_kiosk.html', event=event, token=token)

@app.route('/api/event/<int:event_id>/generate-kiosk-token', methods=['POST'])
@login_required
def generate_kiosk_token(event_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    event = Event.query.get(event_id)
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404

    # Generate secure token
    event.kiosk_token = secrets.token_urlsafe(32)
    # Token expires 24 hours after event ends
    event.kiosk_token_expiry = event.date_time + timedelta(hours=24)

    db.session.commit()

    return jsonify({
        'success': True,
        'token': event.kiosk_token
    })

@app.route('/api/event/<int:event_id>/search-attendees')
def search_attendees(event_id):
    # Validate token
    token = request.args.get('token')
    event = Event.query.get(event_id)

    if not event or event.kiosk_token != token:
        return jsonify({'error': 'Invalid token'}), 403

    if event.kiosk_token_expiry and datetime.utcnow() > event.kiosk_token_expiry:
        return jsonify({'error': 'Token expired'}), 403

    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    # Search users by first or last name (case-insensitive)
    users = User.query.filter(
        or_(
            User.first_name.ilike(f'%{query}%'),
            User.last_name.ilike(f'%{query}%')
        )
    ).limit(5).all()

    results = []
    for user in users:
        # Check RSVP status
        has_rsvp = EventRSVP.query.filter_by(event_id=event_id, user_id=user.id).first() is not None

        # Check if already checked in
        already_checked_in = EventCheckIn.query.filter_by(event_id=event_id, user_id=user.id).first() is not None

        results.append({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_picture': user.profile_picture,
            'has_rsvp': has_rsvp,
            'already_checked_in': already_checked_in
        })

    return jsonify(results)

@app.route('/api/event/<int:event_id>/checkin', methods=['POST'])
def checkin_user(event_id):
    # Validate token
    token = request.args.get('token') or request.json.get('token')
    event = Event.query.get(event_id)

    if not event or event.kiosk_token != token:
        return jsonify({'success': False, 'error': 'Invalid token'}), 403

    if event.kiosk_token_expiry and datetime.utcnow() > event.kiosk_token_expiry:
        return jsonify({'success': False, 'error': 'Token expired'}), 403

    user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'User ID required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Check if already checked in
    existing_checkin = EventCheckIn.query.filter_by(event_id=event_id, user_id=user_id).first()
    if existing_checkin:
        return jsonify({
            'success': True,
            'already_checked_in': True,
            'user_name': user.first_name,
            'message': "You're already checked in!"
        })

    # Check if user had RSVP
    had_rsvp = EventRSVP.query.filter_by(event_id=event_id, user_id=user_id).first() is not None

    # Create check-in record
    checkin = EventCheckIn(
        event_id=event_id,
        user_id=user_id,
        had_rsvp=had_rsvp,
        is_walk_in=False
    )
    db.session.add(checkin)
    db.session.commit()

    return jsonify({
        'success': True,
        'already_checked_in': False,
        'user_name': user.first_name,
        'had_rsvp': had_rsvp,
        'message': 'Check-in successful!'
    })

@app.route('/api/event/<int:event_id>/check-email', methods=['POST'])
def check_email(event_id):
    # Validate token
    token = request.args.get('token') or request.json.get('token')
    event = Event.query.get(event_id)

    if not event or event.kiosk_token != token:
        return jsonify({'success': False, 'error': 'Invalid token'}), 403

    if event.kiosk_token_expiry and datetime.utcnow() > event.kiosk_token_expiry:
        return jsonify({'success': False, 'error': 'Token expired'}), 403

    # Get and sanitize email
    email = sanitize_email(request.json.get('email', ''))

    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400

    # Check if email exists
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        # Check if already checked in to this event
        already_checked_in = EventCheckIn.query.filter_by(
            event_id=event_id,
            user_id=existing_user.id
        ).first() is not None

        return jsonify({
            'exists': True,
            'user': {
                'id': existing_user.id,
                'first_name': existing_user.first_name,
                'last_name': existing_user.last_name,
                'email': existing_user.email,
                'already_checked_in': already_checked_in
            }
        })
    else:
        return jsonify({'exists': False})

@app.route('/api/event/<int:event_id>/checkin-walkin', methods=['POST'])
def checkin_walkin(event_id):
    # Validate token
    token = request.args.get('token') or request.json.get('token')
    event = Event.query.get(event_id)

    if not event or event.kiosk_token != token:
        return jsonify({'success': False, 'error': 'Invalid token'}), 403

    if event.kiosk_token_expiry and datetime.utcnow() > event.kiosk_token_expiry:
        return jsonify({'success': False, 'error': 'Token expired'}), 403

    # Get and sanitize form data
    first_name = sanitize_input(request.json.get('first_name', ''), max_length=100, allow_newlines=False)
    last_name = sanitize_input(request.json.get('last_name', ''), max_length=100, allow_newlines=False)
    email = sanitize_email(request.json.get('email', ''))
    date_of_birth_str = request.json.get('date_of_birth', '').strip()

    # Validate all fields present
    if not all([first_name, last_name, email, date_of_birth_str]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400

    # Validate and parse date of birth
    try:
        date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    # Validate age (must be 18+)
    today = date.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    if age < 18:
        return jsonify({'success': False, 'error': 'You must be at least 18 years old'}), 400

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'success': False, 'error': 'This email is already registered. Please search for your name above.'}), 400

    # Generate username
    base_username = f"{first_name.lower()}.{last_name.lower()}"
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    # Create user account
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        date_of_birth=date_of_birth,
        profile_incomplete=True,
        email_verified=False,
        is_admin=False
    )

    # Generate profile completion token
    token_str = user.generate_profile_completion_token()

    db.session.add(user)
    db.session.commit()

    # Create check-in record
    checkin = EventCheckIn(
        event_id=event_id,
        user_id=user.id,
        had_rsvp=False,
        is_walk_in=True
    )
    db.session.add(checkin)
    db.session.commit()

    # Send welcome email
    profile_completion_url = url_for('complete_profile', token=token_str, _external=True)
    send_walk_in_welcome_email(mail, app.config['MAIL_DEFAULT_SENDER'], user, event.title, profile_completion_url)

    return jsonify({
        'success': True,
        'user_id': user.id,
        'user_name': user.first_name,
        'user_email': user.email,
        'message': 'Check your email to complete your profile!'
    })

@app.route('/complete-profile/<token>', methods=['GET', 'POST'])
@beta_access_required
def complete_profile(token):
    # Find user with this token
    user = User.query.filter_by(profile_completion_token=token).first()

    if not user or not user.verify_profile_completion_token(token):
        flash('Invalid or expired profile completion link. Please contact us for assistance.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Get form data
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        pronouns = sanitize_input(request.form.get('pronouns', ''), max_length=100, allow_newlines=False)
        location = sanitize_location(request.form.get('location', ''))

        # Validate passwords
        if not password or not confirm_password:
            flash('Please fill in all required fields.')
            return redirect(url_for('complete_profile', token=token))

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('complete_profile', token=token))

        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message)
            return redirect(url_for('complete_profile', token=token))

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                is_valid_file, error_msg = validate_file_upload(file.filename)
                if not is_valid_file:
                    flash(error_msg)
                    return redirect(url_for('complete_profile', token=token))

                filename = secure_filename(file.filename)
                unique_filename = f"{user.id}_{filename}"
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                user.profile_picture = f'uploads/{unique_filename}'

        # Update user
        user.set_password(password)
        user.pronouns = pronouns
        user.location = location
        user.profile_incomplete = False
        user.clear_profile_completion_token()

        # Generate email verification token
        verification_token = user.generate_verification_token()

        db.session.commit()

        # Send verification email
        verification_url = url_for('verify_email', token=verification_token, _external=True)
        send_verification_email(mail, app.config['MAIL_DEFAULT_SENDER'], user, verification_url)

        # Log user in
        login_user(user)

        flash('Welcome to Three of Cups! Please complete your assessment to get matched.')

        # Check if user has assessment
        existing_assessment = Assessment.query.filter_by(user_id=user.id).first()
        if existing_assessment:
            return redirect(url_for('user_dashboard'))
        else:
            return redirect(url_for('assessment'))

    # GET request - show form
    # Get event they attended
    latest_checkin = EventCheckIn.query.filter_by(user_id=user.id, is_walk_in=True).order_by(EventCheckIn.checked_in_at.desc()).first()
    event_title = latest_checkin.event.title if latest_checkin else None

    return render_template('complete_profile.html', user=user, event_title=event_title, token=token)

# ─────────────────────────────────────────────────────────────────────────────
# Event Matchmaking Whiteboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/admin/event/<int:event_id>/toggle-matchmaking', methods=['POST'])
@login_required
def toggle_event_matchmaking(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    event = Event.query.get_or_404(event_id)
    event.is_matchmaking = not event.is_matchmaking
    db.session.commit()
    return jsonify({'is_matchmaking': event.is_matchmaking})


@app.route('/admin/event/<int:event_id>/matchmaking')
@login_required
def admin_event_matchmaking(event_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    event = Event.query.get_or_404(event_id)
    return render_template('admin_event_matchmaking.html', event=event)


@app.route('/api/admin/event/<int:event_id>/matchmaking/data')
@login_required
def get_event_matchmaking_data(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    event = Event.query.get_or_404(event_id)
    rsvps = EventRSVP.query.filter_by(event_id=event_id).all()
    rsvp_user_ids = {r.user_id for r in rsvps}

    # Ensure every RSVP'd user has at least one board card
    existing_card_user_ids = {c.user_id for c in EventBoardCard.query.filter_by(event_id=event_id).all()}
    CARD_W, GAP, COLS = 210, 24, 4
    grid_idx = len(existing_card_user_ids)
    for rsvp in rsvps:
        if rsvp.user_id not in existing_card_user_ids:
            col = grid_idx % COLS
            row = grid_idx // COLS
            db.session.add(EventBoardCard(
                event_id=event_id, user_id=rsvp.user_id,
                pos_x=GAP + col * (CARD_W + GAP),
                pos_y=GAP + row * 119,
            ))
            grid_idx += 1
    db.session.commit()

    board_cards = EventBoardCard.query.filter_by(event_id=event_id).order_by(EventBoardCard.id).all()
    # Count instances per user for the badge
    instance_counts = {}
    for c in board_cards:
        instance_counts[c.user_id] = instance_counts.get(c.user_id, 0) + 1

    cards_data = []
    for card in board_cards:
        user = User.query.get(card.user_id)
        if not user:
            continue
        has_assessment = Assessment.query.filter_by(user_id=user.id).first() is not None
        cards_data.append({
            'card_id': card.id,
            'id':      user.id,   # kept for JS backwards-compat (= user_id)
            'user_id': user.id,
            'name':    f"{user.first_name} {user.last_name}",
            'email':   user.email,
            'profile_picture': user.profile_picture,
            'has_assessment':  has_assessment,
            'x':  card.pos_x,
            'y':  card.pos_y,
            'is_rsvp':        user.id in rsvp_user_ids,
            'instance_count': instance_counts[user.id],
        })

    drafts = EventMatchmakingDraft.query.filter_by(event_id=event_id).all()
    matches_data = []
    for draft in drafts:
        try:
            notes = json.loads(draft.notes) if draft.notes else {'similarities': '', 'challenges': ''}
        except Exception:
            notes = {'similarities': draft.notes or '', 'challenges': ''}
        matches_data.append({'id': draft.id, 'user1_id': draft.user1_id,
                             'user2_id': draft.user2_id, 'notes': notes,
                             'card1_id': draft.card1_id, 'card2_id': draft.card2_id})

    return jsonify({
        'event': {'id': event.id, 'title': event.title},
        'cards': cards_data,
        'matches': matches_data,
    })


@app.route('/api/admin/event/<int:event_id>/matchmaking/position', methods=['POST'])
@login_required
def save_board_position(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    x = float(data.get('x', 100))
    y = float(data.get('y', 100))
    card_id = data.get('card_id')
    if card_id:
        card = EventBoardCard.query.filter_by(id=int(card_id), event_id=event_id).first()
        if card:
            card.pos_x, card.pos_y = x, y
            db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/event/<int:event_id>/matchmaking/duplicate-card', methods=['POST'])
@login_required
def duplicate_board_card(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data    = request.get_json()
    card_id = int(data.get('card_id'))
    orig    = EventBoardCard.query.filter_by(id=card_id, event_id=event_id).first_or_404()
    dup     = EventBoardCard(event_id=event_id, user_id=orig.user_id,
                             pos_x=orig.pos_x + 234, pos_y=orig.pos_y + 24)
    db.session.add(dup)
    db.session.commit()
    user           = User.query.get(dup.user_id)
    has_assessment = Assessment.query.filter_by(user_id=dup.user_id).first() is not None
    instance_count = EventBoardCard.query.filter_by(event_id=event_id, user_id=dup.user_id).count()
    # Update instance_count on all cards for this user
    return jsonify({
        'card_id': dup.id, 'id': user.id, 'user_id': user.id,
        'name': f"{user.first_name} {user.last_name}", 'email': user.email,
        'profile_picture': user.profile_picture, 'has_assessment': has_assessment,
        'x': dup.pos_x, 'y': dup.pos_y, 'is_rsvp': True,
        'instance_count': instance_count,
    })


@app.route('/api/admin/event/<int:event_id>/matchmaking/card/<int:card_id>', methods=['DELETE'])
@login_required
def delete_board_card(event_id, card_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    card    = EventBoardCard.query.filter_by(id=card_id, event_id=event_id).first_or_404()
    user_id = card.user_id
    remaining = EventBoardCard.query.filter_by(event_id=event_id, user_id=user_id).count()
    db.session.delete(card)
    removed_rsvp = False
    if remaining == 1:   # this was the last card → remove RSVP too
        rsvp = EventRSVP.query.filter_by(event_id=event_id, user_id=user_id).first()
        if rsvp:
            db.session.delete(rsvp)
            removed_rsvp = True
    db.session.commit()
    return jsonify({'ok': True, 'removed_rsvp': removed_rsvp})


@app.route('/api/admin/event/<int:event_id>/matchmaking/add-user', methods=['POST'])
@login_required
def matchmaking_add_user(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data    = request.get_json()
    user_id = int(data.get('user_id'))
    user    = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not EventRSVP.query.filter_by(event_id=event_id, user_id=user_id).first():
        db.session.add(EventRSVP(event_id=event_id, user_id=user_id))
    existing_count = EventBoardCard.query.filter_by(event_id=event_id).count()
    COLS, CARD_W, GAP = 4, 210, 24
    col = existing_count % COLS
    row = existing_count // COLS
    card = EventBoardCard(event_id=event_id, user_id=user_id,
                          pos_x=GAP + col * (CARD_W + GAP), pos_y=GAP + row * 119)
    db.session.add(card)
    db.session.commit()
    has_assessment = Assessment.query.filter_by(user_id=user_id).first() is not None
    instance_count = EventBoardCard.query.filter_by(event_id=event_id, user_id=user_id).count()
    return jsonify({
        'card_id': card.id, 'id': user.id, 'user_id': user.id,
        'name': f"{user.first_name} {user.last_name}", 'email': user.email,
        'profile_picture': user.profile_picture, 'has_assessment': has_assessment,
        'x': card.pos_x, 'y': card.pos_y, 'is_rsvp': True,
        'instance_count': instance_count,
    })


@app.route('/api/admin/event/<int:event_id>/matchmaking/users-to-add')
@login_required
def matchmaking_users_to_add(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    on_board = {c.user_id for c in EventBoardCard.query.filter_by(event_id=event_id).all()}
    all_users = User.query.order_by(User.last_name, User.first_name).all()
    return jsonify([
        {'id': u.id, 'name': f"{u.first_name} {u.last_name}", 'email': u.email}
        for u in all_users if u.id not in on_board
    ])


@app.route('/api/admin/event/<int:event_id>/matchmaking/match', methods=['POST'])
@login_required
def create_draft_match(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    u1 = int(data.get('user1_id'))
    u2 = int(data.get('user2_id'))
    c1 = data.get('card1_id')
    c2 = data.get('card2_id')
    if u1 == u2:
        return jsonify({'error': 'Cannot match a user with themselves'}), 400
    # Canonical ordering so (A,B) and (B,A) are the same pair
    if u1 > u2:
        u1, u2 = u2, u1
        c1, c2 = c2, c1
    existing = EventMatchmakingDraft.query.filter_by(event_id=event_id, user1_id=u1, user2_id=u2).first()
    if existing:
        return jsonify({'error': 'Match already exists', 'id': existing.id}), 409
    draft = EventMatchmakingDraft(
        event_id=event_id,
        user1_id=u1,
        user2_id=u2,
        card1_id=int(c1) if c1 is not None else None,
        card2_id=int(c2) if c2 is not None else None,
        notes=json.dumps({'similarities': '', 'challenges': ''}),
    )
    db.session.add(draft)
    db.session.commit()
    return jsonify({'id': draft.id, 'user1_id': u1, 'user2_id': u2,
                    'card1_id': draft.card1_id, 'card2_id': draft.card2_id,
                    'notes': {'similarities': '', 'challenges': ''}})


@app.route('/api/admin/event/<int:event_id>/matchmaking/match/<int:draft_id>', methods=['PUT', 'DELETE'])
@login_required
def update_draft_match(event_id, draft_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    draft = EventMatchmakingDraft.query.filter_by(id=draft_id, event_id=event_id).first_or_404()
    if request.method == 'DELETE':
        db.session.delete(draft)
        db.session.commit()
        return jsonify({'ok': True})
    # PUT – update notes
    data = request.get_json()
    raw = data.get('notes', {})
    draft.notes = json.dumps({
        'similarities': sanitize_input(str(raw.get('similarities', '')))[:2000],
        'challenges': sanitize_input(str(raw.get('challenges', '')))[:2000],
    })
    draft.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/event/<int:event_id>/matchmaking/finalize', methods=['POST'])
@login_required
def finalize_event_matches(event_id):
    """Convert all draft match pairs into pending Match records."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    drafts = EventMatchmakingDraft.query.filter_by(event_id=event_id).all()
    created, errors = [], []
    for draft in drafts:
        u1 = User.query.get(draft.user1_id)
        u2 = User.query.get(draft.user2_id)
        a1 = Assessment.query.filter_by(user_id=draft.user1_id).first()
        a2 = Assessment.query.filter_by(user_id=draft.user2_id).first()
        if not a1 or not a2:
            missing = []
            if not a1:
                missing.append(f"{u1.first_name} {u1.last_name}" if u1 else f"User {draft.user1_id}")
            if not a2:
                missing.append(f"{u2.first_name} {u2.last_name}" if u2 else f"User {draft.user2_id}")
            errors.append(f"No assessment for: {', '.join(missing)}")
            continue
        # Skip if a Match already exists for this pair
        already = Match.query.filter(
            or_(
                and_(Match.user1_id == draft.user1_id, Match.user2_id == draft.user2_id),
                and_(Match.user1_id == draft.user2_id, Match.user2_id == draft.user1_id),
            )
        ).first()
        if already:
            errors.append(f"Match already exists for {u1.first_name} & {u2.first_name}")
            continue
        try:
            notes_obj = json.loads(draft.notes) if draft.notes else {}
        except Exception:
            notes_obj = {}
        admin_notes_parts = []
        if notes_obj.get('similarities'):
            admin_notes_parts.append(f"Similarities: {notes_obj['similarities']}")
        if notes_obj.get('challenges'):
            admin_notes_parts.append(f"Potential challenges: {notes_obj['challenges']}")
        match = Match(
            user1_id=draft.user1_id,
            user2_id=draft.user2_id,
            assessment1_id=a1.id,
            assessment2_id=a2.id,
            status='pending',
            admin_notes='\n'.join(admin_notes_parts) or None,
        )
        db.session.add(match)
        name1 = f"{u1.first_name} {u1.last_name}" if u1 else str(draft.user1_id)
        name2 = f"{u2.first_name} {u2.last_name}" if u2 else str(draft.user2_id)
        created.append(f"{name1} & {name2}")
    db.session.commit()
    return jsonify({'created': created, 'errors': errors})


@app.route('/api/admin/event/<int:event_id>/matchmaking/positions', methods=['POST'])
@login_required
def save_board_positions_bulk(event_id):
    """Bulk-save card positions (used by arrange/reset)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json(force=True) or {}
    positions = data.get('positions', [])
    for item in positions:
        card = EventBoardCard.query.filter_by(id=item.get('card_id'), event_id=event_id).first()
        if card:
            card.pos_x = float(item.get('x', 100))
            card.pos_y = float(item.get('y', 100))
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/admin/event/<int:event_id>/matchmaking/reset', methods=['POST'])
@login_required
def reset_matchmaking_board(event_id):
    """Delete all draft matches and reset card positions to default so the frontend can re-arrange."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    EventMatchmakingDraft.query.filter_by(event_id=event_id).delete()
    EventBoardCard.query.filter_by(event_id=event_id).update({'pos_x': 100.0, 'pos_y': 100.0})
    db.session.commit()
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run()
