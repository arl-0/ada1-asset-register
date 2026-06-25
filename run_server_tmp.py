import os
os.environ['SECRET_KEY'] = 'demo-secret-key-for-screenshots'
from app import create_app

app = create_app()
app.config['DEBUG_BYPASS_STARTUP'] = True
app.run(host='127.0.0.1', port=5055)
