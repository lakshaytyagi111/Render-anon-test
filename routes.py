from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from flask_login import login_required
from flask import jsonify
from flask_socketio import emit, join_room, leave_room
from extensions import socketio
from extensions import db
import firebase_admin
from firebase_admin import auth
from google.cloud.firestore_v1.base_query import FieldFilter
import json
from datetime import datetime
import uuid

bp = Blueprint('main', __name__)

# @bp.route("/firestore-test")
# def test_firestore_call():
#     try:
#         docs = db.collection("users").limit(1).get()
#         data = [doc.to_dict() for doc in docs]
#         return jsonify({"status": "success", "data": data, "count": len(data)})
#     except Exception as e:
#         print("Firestore error:", e)
#         import traceback; traceback.print_exc()
#         return jsonify({"status": "error", "message": str(e)}), 500
    

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
        room = get_all_rooms()
        return render_template('index.html', user=session['user'], rooms=room)
    return redirect(url_for('main.login'))

@login_required
@bp.route('/get_chats/<room>')
def get_chats(room):
    chats = get_chats_by_room(room)
    return jsonify(chats)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        displayName = data.get('displayName')
        uid = data.get('uid')
        try:
            
            if data.get('emailVerified') == True:
                print('email verified')
                existing_user = get_user_by_email(email)
                if existing_user:
                    print(f'existing user: {existing_user}')
                if existing_user:
                    user_id = existing_user['id']
                    session['user'] = {
                        'email': email,
                        'anonymous_userid': existing_user['anonymous_userid'],
                        'user_id': user_id
                    }
                    
                else:
                    
                    user_id = str(uuid.uuid4())
                    user_data = {
                        'id': user_id,
                        'email': email,
                        'displayName': displayName,
                        'anonymous_userid': str(uuid.uuid4()),
                        'google_uid': uid,
                        'created_at': datetime.now()
                    }
                    db.collection('users').document(user_id).set(user_data)
                    
                    session['user'] = {
                        'email': email,
                        'anonymous_userid': existing_user['anonymous_userid'],
                        'user_id': existing_user['id']
                    }
                print(session)
                return jsonify({
                    'success': True,
                    'user_id': user_id,
                    'is_new_user': existing_user is None,
                    'redirect': url_for('main.index')
                })
            else:
                return jsonify({'success': False, 'error': 'not verified'}), 400
                
        except Exception as e:
            print(f'Error: {e}')
            return jsonify({'success': False, 'error': 'error during auth'}), 500
            
    return render_template('login.html')

# @bp.route('/send_message', methods=['POST'])
# def send_message():
#     if 'user' not in session:
#         return redirect(url_for('main.login'))
#     data = request.get_json()
#     message = data.get('message')
#     roomId = data.get('roomId')
#     sender = session.get('user', 'Anonymous')
#     timestamp = datetime.now()
    
#     if not message or not roomId:
#         return redirect(url_for('main.index', error="No Content"))
    
#     if not moderate_message(message):
#         chat_rooms[roomId].append({
#                 'sender': sender,
#                 'message': message,
#                 'timestamp': timestamp,
#                 'moderated': True
#             })
#         return redirect(url_for('main.index', error="Message May Contain Hateful Or Inappropriate Speech"))
#     else:
#         if roomId in chat_rooms:
#             chat_rooms[roomId].append({
#                 'sender': sender,
#                 'message': message,
#                 'timestamp': timestamp,
#                 'moderated': False
#             })
#         else:
#             return redirect(url_for('main.index', error="Invalid RoomId"))

#     return redirect(url_for('main.index'))

@bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main.login'))

def get_room(room_id):
    doc = db.collection('rooms').document(room_id).get()
    return doc.to_dict() if doc.exists else None

def get_all_rooms():
    docs = db.collection('rooms').stream()
    docs_list = list(docs)
    print(f'document list :{docs_list}')
    return [doc.to_dict() for doc in docs_list]

def get_chats_by_room(room_id):
    try:
        docs = db.collection('chats').where('room_id', '==', room_id).order_by('timestamp').stream()
        chats = []
        for doc in docs:
            chat_data = doc.to_dict()
            if 'timestamp' in chat_data and chat_data['timestamp']:
                chat_data['timestamp'] = chat_data['timestamp'].isoformat()
                
            chats.append(chat_data)
        return chats
    
    except Exception as e:
        print(f"Error getting chats: {e}")
        docs = db.collection('chats').where('room_id', '==', room_id).stream()
        chats = [doc.to_dict() for doc in docs]
        return sorted(chats, key=lambda x: x.get('timestamp', datetime.min))

def add_chat(room_id, anonymous_userid, message):
    chat_data = {
        'room_id': room_id,
        'anonymous_userid': anonymous_userid,
        'message': message,
        'timestamp': datetime.now()
    }
    print(chat_data)
    db.collection('chats').add(chat_data)
    return True

def get_user_by_email(email):
    print(f'getting users for {email}')
    # docs = db.collection('users').where(filter=("email", "==", email)).limit(1).stream()
    docs = db.collection('users').where(filter=FieldFilter("email", "==", email)).limit(1).stream()
    print("Query executed, iterating...")
    print(docs)
    if docs:
        for doc in docs:
            print(doc.to_dict())
            return doc.to_dict()
    return None

# @socketio.on('join')
# def handle_join(data):
#     room = data['room']
#     join_room(room)
#     emit('status', {'msg': f"{session.get('user', {}).get('anonymous_userid')} has entered the room."}, to=room)

# @socketio.on('leave')
# def handle_leave(data):
#     room = data['room']
#     leave_room(room)
#     emit('status', {'msg': f"{session.get('user', {}).get('anonymous_userid')} has left the room."}, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    anonymous_userid = session.get('user', {}).get('anonymous_userid')
    add_chat(room, anonymous_userid, msg)
    # moderation
    emit('message', {'msg': msg, 'anonymous_userid': 'vhjj j'}, to=room)