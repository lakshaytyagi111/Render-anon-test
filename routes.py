from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from flask_login import login_required
from flask import jsonify
from flask_socketio import emit, join_room, leave_room
from extensions import socketio 
import firebase_admin
from firebase_admin import credentials, auth
import json
from datetime import datetime

cred = credentials.Certificate("/etc/secrets/admin-sdk.json")
firebase_admin.initialize_app(cred)

bp = Blueprint('main', __name__)

# Dummy user database for demonstration
users = {}
rooms = {
    "general": {
        "name": "General Chat",
        "roomId": "6utcyasguxaksj"
    },
    "academics": {
        "name": "Academic Help",
        "roomId": "3w45e6dutvgjhj"
    },
    "complaints": {
        "name": "Raise Concerns",
        "roomId": "6ut9087tfvyjjbj"
    }
}
chat_rooms = {
    "6utcyasguxaksj": [
        {"sender": "System", "message": "Welcome to the General room."},
    ],
    "3w45e6dutvgjhj": [
        {"sender": "System", "message": "Discuss academic questions here."},
        {"sender": "Anon312", "message": "What is the timetable for tomorrow?."}

    ],
    "6ut9087tfvyjjbj": [
        {"sender": "System", "message": "Raise your concerns anonymously."},
        {"sender": "Anon213", "message": "Classroom AC is not working"}
    ]
}
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
        return render_template('index.html', user=session['user'], rooms=rooms)
    return redirect(url_for('main.login'))

@login_required
@bp.route('/get_chats/<room>')
def get_chats(room):
    chats = chat_rooms.get(room, [])
    return jsonify(chats)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        displayName = data.get('displayName')
        print(json.dumps(data, indent=4))
        try:
            
            if data.get('emailVerified') == True:
                session['user'] = {
                    'email': email,
                    'displayName': displayName
                    }
                print(session)
                return render_template('index.html', user=session['user'])
            
        except:
            print('error')
            render_template('login.html', error="Error During Auth.")
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
    data = request.get_json()
    message = data.get('message')
    roomId = data.get('roomId')
    sender = session.get('user', 'Anonymous')
    timestamp = datetime.now()
    
    if not message or not roomId:
        return redirect(url_for('main.index', error="No Content"))
    
    if not moderate_message(message):
        chat_rooms[roomId].append({
                'sender': sender,
                'message': message,
                'timestamp': timestamp,
                'moderated': True
            })
        return redirect(url_for('main.index', error="Message May Contain Hateful Or Inappropriate Speech"))
    else:
        if roomId in chat_rooms:
            chat_rooms[roomId].append({
                'sender': sender,
                'message': message,
                'timestamp': timestamp,
                'moderated': False
            })
        else:
            return redirect(url_for('main.index', error="Invalid RoomId"))

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