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

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answers = db.Column(db.Text)
    reviewed = db.Column(db.Boolean, default=False)
    matched_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

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
