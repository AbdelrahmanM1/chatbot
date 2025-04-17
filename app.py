from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from googleapiclient.discovery import build
import markdown
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdasdafsdfsfdsdsf')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Google Custom Search API setup
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    messages = db.relationship('Message', backref='user', lazy=True)
    search_history = db.relationship('SearchHistory', back_populates='user', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response = db.Column(db.Text)
    user = db.relationship('User', back_populates='search_history')

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('chat'))
        flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        user_message = request.form.get('message')
        if user_message:
            # Get AI response
            response = get_ai_response(user_message)
            
            # Save to search history
            search_entry = SearchHistory(
                user_id=current_user.id,
                query=user_message,
                response=response
            )
            db.session.add(search_entry)
            db.session.commit()
            
            return jsonify({'response': response})
    
    # Check if this is the first visit to chat
    first_visit = not db.session.query(SearchHistory).filter_by(user_id=current_user.id).first()
    welcome_message = "Hi there! How can I help you?"
    
    if first_visit:
        # Save welcome message to history
        search_entry = SearchHistory(
            user_id=current_user.id,
            query="",
            response=welcome_message
        )
        db.session.add(search_entry)
        db.session.commit()
    
    return render_template('chat.html', welcome_message=welcome_message)

@app.route('/search', methods=['POST'])
@login_required
def search():
    query = request.json.get('query')
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = service.cse().list(q=query, cx=GOOGLE_CSE_ID).execute()
        return jsonify(result.get('items', []))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process_markdown', methods=['POST'])
def process_markdown():
    data = request.get_json()
    content = data.get('content', '')
    html = markdown.markdown(content, extensions=['fenced_code', 'tables', 'codehilite'])
    return jsonify({'html': html})

@app.route('/history')
@login_required
def history():
    search_history = db.session.query(SearchHistory).filter_by(user_id=current_user.id).order_by(SearchHistory.timestamp.desc()).all()
    return render_template('history.html', search_history=search_history)

@app.route('/delete_history/<int:id>', methods=['POST'])
@login_required
def delete_history(id):
    history_item = db.session.query(SearchHistory).get_or_404(id)
    if history_item.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    db.session.delete(history_item)
    db.session.commit()
    return jsonify({'success': True})

# Custom filter for markdown with improved formatting
@app.template_filter('markdown')
def markdown_filter(text):
    if not text:
        return ""
    
    # Convert markdown to HTML
    html = markdown.markdown(text, extensions=[
        'fenced_code',
        'codehilite',
        'tables',
        'nl2br',
        'sane_lists'
    ])
    
    # Add custom styling
    html = html.replace('<code>', '<code class="code-block">')
    html = html.replace('<pre>', '<pre class="pre-block">')
    html = html.replace('<table>', '<table class="table table-bordered">')
    
    return html

def get_ai_response(query):
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower().strip()
    
    # Handle specific conversation patterns
    if query_lower in ['hello', 'hi', 'hey']:
        return "Hi there! How can I help you?"
    elif query_lower in ['how are you?', 'how are you doing?']:
        return "I'm doing great! What about you?"
    elif query_lower in ['good', 'fine', 'great', 'well']:
        return "Nice!"
    elif query_lower in ['who made you?', 'who created you?', 'who is your creator?']:
        return "The bot created by Abdelrahman Moharram"
    
    try:
        # First, try to get a response from Google Search
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = service.cse().list(q=query, cx=GOOGLE_CSE_ID).execute()
        
        # Format the response in markdown
        if 'items' in result and result['items']:
            response = "Here's what I found:\n\n"
            for i, item in enumerate(result['items'][:3], 1):
                response += f"### {i}. [{item['title']}]({item['link']})\n\n"
                response += f"{item['snippet']}\n\n"
                if 'pagemap' in item and 'metatags' in item['pagemap']:
                    metatags = item['pagemap']['metatags'][0]
                    if 'og:image' in metatags:
                        response += f"![Preview]({metatags['og:image']})\n\n"
            return response
        else:
            return "I couldn't find any specific information about that. Could you please rephrase your question or try a different topic?"
    except Exception as e:
        print(f"Error in get_ai_response: {str(e)}")
        return "I'm sorry, I encountered an error while processing your request. Please try again later."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 