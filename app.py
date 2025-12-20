from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
import os
import json
import re
import statistics
from datetime import datetime, date
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail
from dotenv import load_dotenv
from models import db, User, Assessment, ReviewerAssessment, Match, Event, EventRSVP
from email_helper import send_password_reset_email, send_match_notification_email, send_verification_email, send_email_change_notification, send_email_change_verification
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
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Email configuration
# NOTE: Update these with your actual email credentials in .env file
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
# Use MAIL_DEFAULT_SENDER if set, otherwise fallback to MAIL_USERNAME
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')

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

def format_draft_email_to_html(plain_text):
    """
    Convert plain text draft email to formatted HTML with Three of Cups styling.
    Uses the app's peachy color palette: #FF9B9B (coral), #FFB88C (peach), #FFD97D (yellow)
    """
    if not plain_text:
        return ""

    # Escape any existing HTML to prevent issues
    import html
    text = html.escape(plain_text)

    # Split into paragraphs (double newlines)
    paragraphs = text.split('\n\n')

    html_parts = []
    html_parts.append('<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #2C2420;">')

    for para in paragraphs:
        if not para.strip():
            continue

        # Check if this looks like a heading (short line, possibly ending with :)
        if len(para.strip()) < 60 and (para.strip().endswith(':') or para.strip().endswith('!')):
            html_parts.append(f'<h3 style="color: #FF9B9B; margin-top: 25px; margin-bottom: 15px;">{para.strip()}</h3>')
        # Check if it's a bulleted list
        elif '•' in para or para.strip().startswith('-'):
            items = [line.strip().lstrip('•-').strip() for line in para.split('\n') if line.strip()]
            if items:
                html_parts.append('<ul style="margin: 15px 0; padding-left: 20px;">')
                for item in items:
                    html_parts.append(f'<li style="margin: 8px 0;">{item}</li>')
                html_parts.append('</ul>')
        # Check if it looks like a special callout (contains "awareness" or "note")
        elif 'awareness' in para.lower() or 'gentle' in para.lower() or 'note:' in para.lower():
            formatted_para = para.replace('\n', '<br>')
            html_parts.append(f'<div style="background-color: #FFF7ED; padding: 15px; border-left: 4px solid #FFB88C; border-radius: 4px; margin: 20px 0;">{formatted_para}</div>')
        # Check if it looks like contact info
        elif 'contact' in para.lower() and 'info' in para.lower():
            formatted_para = para.replace('\n', '<br>')
            html_parts.append(f'<div style="background-color: #FAF7F5; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #FFD97D;">{formatted_para}</div>')
        # Check if it's the signature (contains "Iris" or ends with emoji)
        elif 'iris' in para.lower() or '🌟' in para or para.strip().startswith('With '):
            formatted_para = para.replace('\n', '<br>')
            html_parts.append(f'<hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;"><p style="font-style: italic; color: #FF9B9B;">{formatted_para}</p>')
        # Regular paragraph
        else:
            formatted_para = para.replace('\n', '<br>')
            html_parts.append(f'<p style="margin: 15px 0; line-height: 1.6;">{formatted_para}</p>')

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
        if User.query.filter_by(email=email).first():
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

        if user and user.check_password(password):
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
@login_required
def assessment():
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

    # Add filter for assessment status
    filter_status = request.args.get('filter', 'unreviewed')
    if filter_status == 'all':
        assessments = Assessment.query.all()
    elif filter_status == 'reviewed':
        assessments = Assessment.query.filter_by(reviewed=True).all()
    else:  # Default to unreviewed
        assessments = Assessment.query.filter_by(reviewed=False).all()
    users = User.query.all()

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

    return render_template('admin_assessments.html',
                         assessments_with_scores=assessments_with_scores,
                         users=users,
                         user_match_counts=user_match_counts,
                         user_existing_matches=user_existing_matches,
                         user_previous_matches=user_previous_matches,
                         filter_status=filter_status)

# Admin matches page
@app.route('/admin/matches')
@login_required
def admin_matches():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    # Get finalized matches from Match table
    finalized_matches = Match.query.filter_by(status='finalized').all()

    # Build match data with user information
    matches_data = []
    for match in finalized_matches:
        user1 = User.query.get(match.user1_id)
        user2 = User.query.get(match.user2_id)
        if user1 and user2:
            matches_data.append({
                'match': match,
                'user1': user1,
                'user2': user2
            })

    return render_template('admin_matches.html', matches_data=matches_data)

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

    # Check if each user has any other finalized matches
    # If not, set their assessment back to unreviewed
    user1_other_matches = Match.query.filter(
        Match.status == 'finalized',
        or_(Match.user1_id == match.user1_id, Match.user2_id == match.user1_id),
        Match.id != match_id
    ).first()

    user2_other_matches = Match.query.filter(
        Match.status == 'finalized',
        or_(Match.user1_id == match.user2_id, Match.user2_id == match.user2_id),
        Match.id != match_id
    ).first()

    # If user1 has no other matches, mark their assessment as unreviewed
    if not user1_other_matches and assessment1:
        assessment1.reviewed = False

    # If user2 has no other matches, mark their assessment as unreviewed
    if not user2_other_matches and assessment2:
        assessment2.reviewed = False

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Match successfully unmatched',
        'user1_assessment_unreviewed': not user1_other_matches,
        'user2_assessment_unreviewed': not user2_other_matches
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

            # Use the drafted email if available, otherwise use default template
            if match.draft_email:
                # Send custom drafted email to both users
                from flask_mail import Message
                for user in [user1, user2]:
                    if user:
                        try:
                            # Determine the match's name (the other person)
                            match_name = user2.first_name if user.id == user1.id else user1.first_name

                            msg = Message(
                                f'Your Three of Cups Match: Meet {match_name}!',
                                sender=app.config['MAIL_DEFAULT_SENDER'],
                                recipients=[user.email]
                            )
                            # Replace placeholders in draft email
                            personalized_email = match.draft_email.replace('{first_name}', user.first_name)
                            personalized_email = personalized_email.replace('{match_name}', match_name)
                            personalized_email = personalized_email.replace('{dashboard_url}', dashboard_url)
                            msg.body = personalized_email
                            # Convert to formatted HTML with Three of Cups styling
                            msg.html = format_draft_email_to_html(personalized_email)

                            # Send email first (priority)
                            mail.send(msg)

                            # Then store the HTML content
                            if user.id == user1.id:
                                match.user1_email_content = msg.html
                            else:
                                match.user2_email_content = msg.html
                        except Exception as e:
                            print(f"Error sending custom match email: {e}")
            else:
                # Use default template
                if user1:
                    success, html_content = send_match_notification_email(mail, app.config['MAIL_DEFAULT_SENDER'], user1, user2.first_name, dashboard_url)
                    if success and html_content:
                        match.user1_email_content = html_content
                if user2:
                    success, html_content = send_match_notification_email(mail, app.config['MAIL_DEFAULT_SENDER'], user2, user1.first_name, dashboard_url)
                    if success and html_content:
                        match.user2_email_content = html_content

            # Commit to database after emails are sent
            db.session.commit()

            flash('Match finalized successfully! Emails sent to both users.')

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
                    matched_users.append({
                        'user': matched_user,
                        'match_id': match.id
                    })

        # Get user's RSVP'd events
        user_rsvps = EventRSVP.query.filter_by(user_id=current_user.id).all()
        rsvp_event_ids = [rsvp.event_id for rsvp in user_rsvps]

        # Get upcoming events user has RSVP'd to
        upcoming_rsvp_events = Event.query.filter(
            Event.id.in_(rsvp_event_ids),
            Event.date_time >= datetime.utcnow()
        ).order_by(Event.date_time.asc()).all() if rsvp_event_ids else []

        # Get past events user has RSVP'd to
        past_rsvp_events = Event.query.filter(
            Event.id.in_(rsvp_event_ids),
            Event.date_time < datetime.utcnow()
        ).order_by(Event.date_time.desc()).all() if rsvp_event_ids else []

    return render_template('user_dashboard.html',
                         matched_users=matched_users,
                         results_data=results_data,
                         email_verified=current_user.email_verified,
                         upcoming_rsvp_events=upcoming_rsvp_events,
                         past_rsvp_events=past_rsvp_events)

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
    # Get all upcoming events (future events only)
    from sqlalchemy import or_
    upcoming_events = Event.query.filter(
        Event.date_time >= datetime.utcnow()
    ).order_by(Event.date_time.asc()).all()

    # Get user's RSVPs if authenticated
    user_rsvps = set()
    if current_user.is_authenticated:
        rsvps = EventRSVP.query.filter_by(user_id=current_user.id).all()
        user_rsvps = {rsvp.event_id for rsvp in rsvps}

    # Get RSVP counts for each event
    event_rsvp_counts = {}
    for event in upcoming_events:
        count = EventRSVP.query.filter_by(event_id=event.id).count()
        event_rsvp_counts[event.id] = count

    return render_template('events.html',
                         events=upcoming_events,
                         user_rsvps=user_rsvps,
                         event_rsvp_counts=event_rsvp_counts)

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
        location = sanitize_location(request.form.get('location', ''))
        date_time_str = request.form.get('date_time', '').strip()
        price_str = request.form.get('price', '').strip()

        # Validate required fields
        if not all([title, description, location, date_time_str]):
            flash('Title, description, location, and date/time are required.')
            return redirect(url_for('admin_events'))

        # Parse date/time
        try:
            event_date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format.')
            return redirect(url_for('admin_events'))

        # Parse price (optional)
        price = None
        if price_str:
            try:
                price = float(price_str)
                if price < 0:
                    flash('Price cannot be negative.')
                    return redirect(url_for('admin_events'))
            except ValueError:
                flash('Invalid price format.')
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
            date_time=event_date_time,
            price=price,
            picture=picture,
            created_by=current_user.id
        )
        db.session.add(new_event)
        db.session.commit()

        flash('Event created successfully!')
        return redirect(url_for('admin_events'))

    # Get all events (past and future)
    all_events = Event.query.order_by(Event.date_time.desc()).all()

    # Get RSVP counts and lists for each event
    event_data = []
    for event in all_events:
        rsvps = EventRSVP.query.filter_by(event_id=event.id).all()
        rsvp_users = []
        for rsvp in rsvps:
            user = User.query.get(rsvp.user_id)
            if user:
                rsvp_users.append(user)

        event_data.append({
            'event': event,
            'rsvp_count': len(rsvps),
            'rsvp_users': rsvp_users
        })

    return render_template('admin_events.html', event_data=event_data, now=datetime.utcnow())

@app.route('/api/event/rsvp/<int:event_id>', methods=['POST'])
@login_required
def rsvp_event(event_id):
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

    # Create RSVP
    rsvp = EventRSVP(event_id=event_id, user_id=current_user.id)
    db.session.add(rsvp)
    db.session.commit()

    return jsonify({'success': True, 'message': 'RSVP successful!'})

@app.route('/api/event/unrsvp/<int:event_id>', methods=['POST'])
@login_required
def unrsvp_event(event_id):
    rsvp = EventRSVP.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()

    if not rsvp:
        return jsonify({'error': 'RSVP not found'}), 404

    db.session.delete(rsvp)
    db.session.commit()

    return jsonify({'success': True, 'message': 'RSVP removed successfully!'})

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

if __name__ == '__main__':
    app.run(debug=True)
