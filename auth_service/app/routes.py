from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.auth_utils import (
    hash_password, verify_password, create_access_token,
    blacklist_token)
from app.models import User
from app.database import get_db

router = APIRouter()

@router.post("/signup")
def signup(username: str, email: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(username=username, email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    return {"msg": "User created"}

@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid Authorization header")
    token = authorization.replace("Bearer ", "")
    blacklist_token(token)
    return {"msg": "Logged out"}

@router.route('/health')
def health_check():
    return "OK", 200