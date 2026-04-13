try:
    import eventlet
    eventlet.monkey_patch()
except Exception as e:
    print(f"[WSGI] Eventlet indisponible localement: {e}")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_dotenv

load_dotenv()

from app import app, socketio, start_runtime_services

start_runtime_services()

# WSGI application pour gunicorn
application = app
