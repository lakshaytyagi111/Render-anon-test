from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from flask_socketio import emit, join_room, leave_room
from extensions import socketio 

bp = Blueprint('main', __name__)

# Dummy user database for demonstration
users = {}

def moderate_message(message):
    # Placeholder for Gemini API moderation call
    # Replace with actual API integration
    flagged_words = ['abuse', 'hate']
    if any(word in message.lower() for word in flagged_words):
        return False  # Message is flagged
    return True

@bp.route('/')
def index():
    if 'user' in session:
        return render_template('index.html', user=session['user'])
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        # Here, integrate Firebase Auth verification
        session['user'] = {'email': email}
        return render_template('index.html', user=session['user'])
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users[email] = password
        flash('Registered! Please log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@bp.route('/send_message', methods=['POST'])
def send_message():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    message = request.form['message']
    if not moderate_message(message):
        flash('Message flagged by moderation.')
        return redirect(url_for('main.index'))
    # Save message to DB (not implemented)
    flash('Message sent!')
    return redirect(url_for('main.index'))

@bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main.login'))

@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f"{session.get('user', {}).get('email', 'Anonymous')} has entered the room."}, to=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f"{session.get('user', {}).get('email', 'Anonymous')} has left the room."}, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    # Optionally add moderation here
    emit('message', {'msg': msg}, to=room)