from flask import Flask

app = Flask(__name__)
app.secret_key = 'your_flask_secret_key'

from app import routes