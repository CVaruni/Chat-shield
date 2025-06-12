from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from datetime import datetime, timedelta
import os
import json
from spam_detector import SpamDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-keep-it-secret'  # Fixed secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spam_detector.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)  # Sessions last for 31 days
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=31)  # Remember me cookie lasts 31 days
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    messages = db.relationship('Message', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

# Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_spam = db.Column(db.Boolean, default=False)
    spam_score = db.Column(db.Float)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    analysis_details = db.Column(db.JSON)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize spam detector
spam_detector = SpamDetector()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)  # Enable remember me
            return redirect(url_for('check_spam'))
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/check_spam', methods=['GET', 'POST'])
@login_required
def check_spam():
    if request.method == 'POST':
        message_content = request.form.get('message')
        if message_content:
            analysis = spam_detector.analyze_message(message_content)
            
            message = Message(
                content=message_content,
                is_spam=analysis['is_spam'],
                spam_score=analysis['spam_score'],
                analysis_details=analysis['signals'],
                user_id=current_user.id
            )
            db.session.add(message)
            db.session.commit()
            
            return render_template('result.html',
                                 is_spam=analysis['is_spam'],
                                 spam_score=analysis['spam_score'],
                                 analysis=analysis['signals'],
                                 message=message_content,
                                 extracted_numbers=analysis.get('extracted_numbers', []),
                                 suspicious_patterns=analysis.get('suspicious_patterns', []))

    
    return render_template('check_spam.html')

@app.route('/history')
@login_required
def history():
    messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.checked_at.desc()).all()
    return render_template('history.html', messages=messages)

# Initialize admin
from admin import UserAdmin, MessageAdmin, AnalyticsView
admin = Admin(app, name='Spam Detector Admin', template_mode='bootstrap3')
admin.add_view(UserAdmin(User, db.session))
admin.add_view(MessageAdmin(Message, db.session))
admin.add_view(AnalyticsView(name='Analytics', endpoint='analytics'))

@app.route('/api/stats')
@login_required
def get_stats():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    total_messages = Message.query.count()
    spam_messages = Message.query.filter_by(is_spam=True).count()
    recent_messages = Message.query.order_by(Message.checked_at.desc()).limit(5).all()
    
    return jsonify({
        'total_messages': total_messages,
        'spam_messages': spam_messages,
        'spam_ratio': spam_messages / total_messages if total_messages > 0 else 0,
        'recent_messages': [{
            'content': msg.content,
            'is_spam': msg.is_spam,
            'checked_at': msg.checked_at.isoformat()
        } for msg in recent_messages]
    })

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        # Create admin user
        admin_user = User(username='admin', is_admin=True)
        admin_user.password_hash = generate_password_hash('admin123')
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Only create tables if they don't exist
    app.run(debug=True)
