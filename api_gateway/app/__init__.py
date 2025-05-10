from flask import Flask
import redis
import os
from flask_jwt_extended import JWTManager
from app.get_services import register_service, REDIS

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'your_secret_key'
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.secret_key = 'your_secret_key'

jwt = JWTManager(app)

host_name, port = REDIS[0].split(":")
redis_client = redis.Redis(host=host_name, port=port, db=0, decode_responses=True)

port = int(os.getenv("PORT", ""))
service_name = os.getenv("SERVICE_NAME", "")

register_service("api_gateway", service_name, port)

from app import routes
