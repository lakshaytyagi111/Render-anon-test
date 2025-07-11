from flask_socketio import SocketIO
import firebase_admin
from firebase_admin import credentials, firestore
import os
socketio = SocketIO()

if not firebase_admin._apps:
    cred = credentials.Certificate('/etc/secrets/admin-sdk.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()