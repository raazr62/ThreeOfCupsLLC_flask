from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Assessment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///friendship.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Homepage route
@app.route('/')
def home():
    return render_template('index.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
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
        flash('Registration successful.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
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
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# Assessment route
@app.route('/assessment', methods=['GET', 'POST'])
@login_required
def assessment():
    if request.method == 'POST':
        import json
        
        # Collect all assessment responses in structured format
        assessment_data = {}
        
        # Friendship Readiness Scale responses
        assessment_data['friendship_readiness'] = {
            'emotional_energy': request.form.get('emotional_energy'),
            'share_feelings': request.form.get('share_feelings'),
            'bounce_back': request.form.get('bounce_back'),
            'interested_others': request.form.get('interested_others'),
            'make_time': request.form.get('make_time'),
            'follow_through': request.form.get('follow_through'),
            'maintain_effort': request.form.get('maintain_effort'),
            'good_listener': request.form.get('good_listener'),
            'express_needs': request.form.get('express_needs'),
            'handle_disagreements': request.form.get('handle_disagreements')
        }
        
        # Life priorities ranking
        assessment_data['life_priorities'] = {
            'career': request.form.get('priority_career'),
            'family': request.form.get('priority_family'),
            'adventure': request.form.get('priority_adventure'),
            'financial': request.form.get('priority_financial'),
            'growth': request.form.get('priority_growth'),
            'health': request.form.get('priority_health')
        }
        
        # Social preferences
        assessment_data['social_preferences'] = {
            'introversion': request.form.get('introversion'),
            'group_size': request.form.get('group_size'),
            'communication_freq': request.form.get('communication_freq')
        }
        
        # Activity interests
        activities = request.form.getlist('activities')
        assessment_data['activities'] = activities
        
        # Activity preferences
        assessment_data['activity_preferences'] = {
            'indoor_outdoor': request.form.get('indoor_outdoor'),
            'spontaneous_planned': request.form.get('spontaneous_planned')
        }
        
        # Personality traits
        assessment_data['personality'] = {
            'humor_style': request.form.get('humor_style'),
            'risk_taking': request.form.get('risk_taking'),
            'optimism': request.form.get('optimism')
        }
        
        # Multiple choice responses
        assessment_data['preferences'] = {
            'making_friends': request.form.get('making_friends'),
            'conflict_scenario': request.form.get('conflict_scenario'),
            'political_importance': request.form.get('political_importance'),
            'religious_orientation': request.form.get('religious_orientation'),
            'spending_approach': request.form.get('spending_approach')
        }
        
        # Friendship qualities ranking
        assessment_data['friendship_qualities'] = {
            'loyalty': request.form.get('quality_loyalty'),
            'humor': request.form.get('quality_humor'),
            'goals': request.form.get('quality_goals'),
            'support': request.form.get('quality_support'),
            'interests': request.form.get('quality_interests')
        }
        
        # Gender preferences
        gender_preferences = request.form.getlist('gender_preferences')
        assessment_data['gender_preferences'] = gender_preferences
        
        # Convert to JSON string for storage
        answers_json = json.dumps(assessment_data, indent=2)
        
        assessment = Assessment(user_id=current_user.id, answers=answers_json)
        db.session.add(assessment)
        db.session.commit()
        flash('Assessment submitted.')
        return redirect(url_for('user_dashboard'))
    return render_template('assessment.html')

# Admin dashboard route
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('login'))

    assessments = Assessment.query.filter_by(reviewed=False).all()
    users = User.query.all()
    
    # Get completed matches
    completed_matches = Assessment.query.filter(
        Assessment.reviewed == True,
        Assessment.matched_user_id.isnot(None)
    ).all()

    if request.method == 'POST':
        assessment_id = request.form['assessment_id']
        matched_user_id = request.form['matched_user_id']

        assessment = Assessment.query.get(assessment_id)
        if assessment:
            assessment.reviewed = True
            assessment.matched_user_id = matched_user_id
            db.session.commit()
            flash('User matched successfully.')
        else:
            flash('Assessment not found.')

    return render_template('admin_dashboard.html', assessments=assessments, users=users, completed_matches=completed_matches)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    matched_users = []
    user_assessments = Assessment.query.filter_by(user_id=current_user.id, reviewed=True).all()
    for assessment in user_assessments:
        if assessment.matched_user_id:
            matched_user = User.query.get(assessment.matched_user_id)
            if matched_user:
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
        flash('Profile updated successfully.')
        return redirect(url_for('user_dashboard'))
    
    return render_template('user_dashboard.html', matched_users=matched_users)

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
    with app.app_context():
        db.create_all()
    app.run(debug=True)

