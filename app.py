from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
import os
import json
import re
import statistics
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from dotenv import load_dotenv
from models import db, User, Assessment

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///friendship.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
UNDER_CONSTRUCTION = True  # Set to False when ready to launch

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate all fields are provided
        if not all([first_name, last_name, email, username, password, confirm_password]):
            flash('All fields are required.')
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
        user = User(username=username, first_name=first_name, last_name=last_name, email=email, is_admin=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
@beta_access_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

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
            try:
                reset_url = url_for('reset_password', token=token, _external=True)
                msg = Message(
                    'Password Reset Request - Three of Cups',
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[user.email]
                )
                msg.body = f'''Hello {user.first_name},

You requested to reset your password for your Three of Cups account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
the three of cups team
'''
                msg.html = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Password Reset Request</h2>
                    <p>Hello {user.first_name},</p>
                    <p>You requested to reset your password for your Three of Cups account.</p>
                    <p>Click the button below to reset your password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #8B5CF6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">Reset Password</a>
                    </div>
                    <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
                    <p style="color: #8B5CF6; word-break: break-all;">{reset_url}</p>
                    <p style="color: #666; font-size: 14px;">This link will expire in 1 hour.</p>
                    <p style="color: #666; font-size: 14px;">If you did not request this password reset, please ignore this email and your password will remain unchanged.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px;">Best regards,<br>The Three of Cups Team</p>
                </div>
                '''
                mail.send(msg)
            except Exception as e:
                print(f"Error sending email: {e}")
                # Still show success message to user for security

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

# Assessment route
@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
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
                # Multiple values selected
                assessment_data[key] = values
            else:
                # Single value
                assessment_data[key] = request.form.get(key)

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
    completed_matches = Assessment.query.filter(
        Assessment.reviewed == True,
        Assessment.matched_user_id.isnot(None)
    ).count()
    total_users = User.query.filter_by(is_admin=False).count()
    
    return render_template('admin_main.html', 
                         total_assessments=total_assessments,
                         pending_assessments=pending_assessments,
                         completed_matches=completed_matches,
                         total_users=total_users)

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
            assessment.reviewed = True
            assessment.matched_user_id = matched_user_id
            db.session.commit()
            flash('User matched successfully.')
            return redirect(url_for('admin_assessments'))
        else:
            flash('Assessment not found.')

    assessments = Assessment.query.filter_by(reviewed=False).all()
    users = User.query.all()

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
                         users=users)

# Admin matches page  
@app.route('/admin/matches')
@login_required
def admin_matches():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))
        
    completed_matches = Assessment.query.filter(
        Assessment.reviewed == True,
        Assessment.matched_user_id.isnot(None)
    ).all()
    users = User.query.all()
    
    return render_template('admin_matches.html', 
                         completed_matches=completed_matches, 
                         users=users)

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

    # Find matches in two ways:
    # 1. Assessments where current user is matched TO someone
    user_assessments = Assessment.query.filter_by(user_id=current_user.id, reviewed=True).all()
    for assessment in user_assessments:
        if assessment.matched_user_id:
            matched_user = User.query.get(assessment.matched_user_id)
            if matched_user and matched_user.id != current_user.id:
                matched_users.append(matched_user)

    # 2. Assessments where current user IS the match (matched_user_id points to them)
    assessments_matched_to_user = Assessment.query.filter_by(
        matched_user_id=current_user.id,
        reviewed=True
    ).all()
    for assessment in assessments_matched_to_user:
        matched_user = User.query.get(assessment.user_id)
        if matched_user and matched_user.id != current_user.id and matched_user not in matched_users:
            matched_users.append(matched_user)
    
    if request.method == 'POST':
        if 'bio' in request.form:
            current_user.bio = request.form['bio']
            
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{current_user.id}_{filename}"
                
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                current_user.profile_picture = f'uploads/{unique_filename}'
        
        db.session.commit()
        return redirect(url_for('user_dashboard'))
    
    return render_template('user_dashboard.html', 
                         matched_users=matched_users,
                         results_data=results_data)

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
            'profile_picture': user.profile_picture
        },
        'assessment': parsed_answers
    })

if __name__ == '__main__':
    app.run(debug=True)
