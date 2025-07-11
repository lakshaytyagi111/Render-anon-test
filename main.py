import os
from flask import Flask, send_file
from extensions import socketio
from routes import bp
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_is_secret_key'
app.register_blueprint(bp)
socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False)

