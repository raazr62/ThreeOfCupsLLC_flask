from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Increased size for secure password hashes
    is_admin = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(200))
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    pronouns = db.Column(db.String(100), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_token_expiry = db.Column(db.DateTime, nullable=True)
    pending_email = db.Column(db.String(150), nullable=True)
    email_change_token = db.Column(db.String(100), nullable=True)
    email_change_token_expiry = db.Column(db.DateTime, nullable=True)
    can_retake_assessment = db.Column(db.Boolean, default=False)  # Flag to allow assessment retakes
    has_paid = db.Column(db.Boolean, default=False)  # Track if user has paid for match service
    payment_waived_at = db.Column(db.DateTime, nullable=True)  # Timestamp when admin waived payment
    profile_incomplete = db.Column(db.Boolean, default=False)
    profile_completion_token = db.Column(db.String(100), nullable=True)
    profile_completion_token_expiry = db.Column(db.DateTime, nullable=True)
    disclaimer_agreed = db.Column(db.Boolean, default=False)  # Track if user agreed to service disclaimer
    disclaimer_agreed_at = db.Column(db.DateTime, nullable=True)  # When user agreed to disclaimer

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        """Generate a secure password reset token that expires in 1 hour"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if self.reset_token != token:
            return False
        if self.reset_token_expiry is None or datetime.utcnow() > self.reset_token_expiry:
            return False
        return True

    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None

    def generate_verification_token(self):
        """Generate a secure email verification token that expires in 24 hours"""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.verification_token

    def verify_email_token(self, token):
        """Verify if the email verification token is valid and not expired"""
        if self.verification_token != token:
            return False
        if self.verification_token_expiry is None or datetime.utcnow() > self.verification_token_expiry:
            return False
        # Mark email as verified
        self.email_verified = True
        return True

    def clear_verification_token(self):
        """Clear the verification token after use"""
        self.verification_token = None
        self.verification_token_expiry = None

    def generate_email_change_token(self):
        """Generate a secure email change verification token that expires in 24 hours"""
        self.email_change_token = secrets.token_urlsafe(32)
        self.email_change_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.email_change_token

    def verify_email_change_token(self, token):
        """Verify if the email change token is valid and not expired"""
        if self.email_change_token != token:
            return False
        if self.email_change_token_expiry is None or datetime.utcnow() > self.email_change_token_expiry:
            return False
        return True

    def clear_email_change_token(self):
        """Clear the email change token and pending email after use"""
        self.email_change_token = None
        self.email_change_token_expiry = None
        self.pending_email = None

    def generate_profile_completion_token(self):
        """Generate a secure profile completion token that expires in 7 days"""
        self.profile_completion_token = secrets.token_urlsafe(32)
        self.profile_completion_token_expiry = datetime.utcnow() + timedelta(days=7)
        return self.profile_completion_token

    def verify_profile_completion_token(self, token):
        """Verify if the profile completion token is valid and not expired"""
        if self.profile_completion_token != token:
            return False
        if self.profile_completion_token_expiry is None or datetime.utcnow() > self.profile_completion_token_expiry:
            return False
        return True

    def clear_profile_completion_token(self):
        """Clear the profile completion token after use"""
        self.profile_completion_token = None
        self.profile_completion_token_expiry = None

    def can_access_assessment(self):
        """Check if user can access the assessment (hasn't completed it or is allowed to retake)"""
        from models import Assessment
        existing_assessment = Assessment.query.filter_by(user_id=self.id).first()

        # User can access if they haven't taken it yet OR if they're allowed to retake
        return existing_assessment is None or self.can_retake_assessment

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answers = db.Column(db.Text)
    reviewed = db.Column(db.Boolean, default=False)
    matched_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment1_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    assessment2_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending' or 'finalized'
    admin_notes = db.Column(db.Text)
    draft_email = db.Column(db.Text)
    user1_email_content = db.Column(db.Text, nullable=True)  # HTML email sent to user1
    user2_email_content = db.Column(db.Text, nullable=True)  # HTML email sent to user2
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finalized_at = db.Column(db.DateTime, nullable=True)

class ReviewerAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    pronouns = db.Column(db.String(100))
    age_range = db.Column(db.String(50))
    location = db.Column(db.String(200))
    answers = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed = db.Column(db.Boolean, default=False)
    admin_notes = db.Column(db.Text)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(500), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=True)  # NULL means free
    picture = db.Column(db.String(200), nullable=True)
    max_capacity = db.Column(db.Integer, nullable=True)  # NULL means unlimited capacity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kiosk_token = db.Column(db.String(100), nullable=True)
    kiosk_token_expiry = db.Column(db.DateTime, nullable=True)

class EventRSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure a user can only RSVP once per event
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_rsvp'),)

class EventCheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    checked_in_at = db.Column(db.DateTime, default=datetime.utcnow)
    had_rsvp = db.Column(db.Boolean, default=False)
    is_walk_in = db.Column(db.Boolean, default=False)  # Track new user walk-ins

    # Relationships
    event = db.relationship('Event', backref='check_ins')
    user = db.relationship('User', backref='event_check_ins')

    # Unique constraint - one check-in per user per event
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_checkin'),)
