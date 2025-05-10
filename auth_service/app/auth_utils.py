from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import redis
import os
from app.get_redis import REDIS_SERVERS

SECRET_KEY = os.getenv("JWT_SECRET", "default_value_if_not_set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
host_name, port = REDIS_SERVERS[0].split(":")
redis_client = redis.Redis(host=host_name, port=port, db=0, decode_responses=True)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def blacklist_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        ttl = exp - int(datetime.utcnow().timestamp())
        if ttl > 0:
            redis_client.setex(token, ttl, "blacklisted")
    except JWTError:
        pass

def is_token_blacklisted(token: str) -> bool:
    return redis_client.get(token) == "blacklisted"
