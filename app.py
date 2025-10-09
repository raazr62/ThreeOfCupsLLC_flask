from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
import os
import json
import statistics
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Assessment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///friendship.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        is_admin = True if request.form.get('role') == 'admin' else False

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('register'))

        user = User(username=username, first_name=first_name, last_name=last_name, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
@beta_access_required
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
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

        # Collect all assessment responses in structured format
        assessment_data = {}

        # Friendship Likeness (9 questions)
        assessment_data['friendship_likeness'] = {}
        for i in range(1, 10):
            field_name = f'friendship_likeness_q{i}'
            value = request.form.get(field_name)
            print(f"Looking for {field_name}, got: {value}")
            assessment_data['friendship_likeness'][f'q{i}'] = value

        # Personality (20 questions)
        assessment_data['personality'] = {}
        for i in range(1, 21):
            field_name = f'personality_q{i}'
            assessment_data['personality'][f'q{i}'] = request.form.get(field_name)

        # Rupture and Repair (10 questions)
        assessment_data['rupture_repair'] = {}
        for i in range(1, 11):
            field_name = f'rupture_repair_q{i}'
            assessment_data['rupture_repair'][f'q{i}'] = request.form.get(field_name)

        # This or That (16 questions)
        assessment_data['this_or_that'] = {}
        for i in range(1, 17):
            field_name = f'this_or_that_q{i}'
            assessment_data['this_or_that'][f'q{i}'] = request.form.get(field_name)

        # Values (multi-select, exactly 5)
        values = request.form.getlist('values')
        assessment_data['values'] = values

        # Top Friendship Qualities (multi-select, exactly 5)
        top_qualities = request.form.getlist('top_friendship_qualities')
        assessment_data['top_friendship_qualities'] = top_qualities

        # Preferences section (mixed types)
        assessment_data['preferences'] = {
            'gender_preference': request.form.getlist('preferences_gender_preference'),
            'substance_use': request.form.getlist('preferences_substance_use'),
            'religious_preference': request.form.getlist('preferences_religious_preference'),
            'relationship_status': request.form.getlist('preferences_relationship_status'),
            'sexuality_preference': request.form.getlist('preferences_sexuality_preference'),
            'political_leaning': request.form.getlist('preferences_political_leaning'),
            'location_preference': request.form.getlist('preferences_location_preference'),
            'experience_hope': request.form.get('preferences_experience_hope'),
            'team_notes': request.form.get('preferences_team_notes'),
            'dealbreakers': request.form.get('preferences_dealbreakers')
        }

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
