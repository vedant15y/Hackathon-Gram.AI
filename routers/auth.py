from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
import os
from passlib.context import CryptContext
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(
    os.getenv("APP_SESSION_SECRET", "gramai-dev-session-secret"),
    salt="gramai-session",
)
SESSION_MAX_AGE = 60 * 60 * 24 * 30

def hash_pw(pw: str):
    return pwd_context.hash(pw[:72])

def verify_pw(pw: str, hashed: str):
    try:
        return pwd_context.verify(pw[:72], hashed)
    except:
        return False


def create_session_token(user: models.User):
    return serializer.dumps({"user_id": user.id, "email": user.email})


def verify_session_token(token: str):
    return serializer.loads(token, max_age=SESSION_MAX_AGE)

@router.post("/signup")
def signup(data: schemas.UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == data.email).first()
    if db_user:
        return {"status": "fail", "error": "User exists"}
    
    new_user = models.User(email=data.email, password=hash_pw(data.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "status": "success",
        "user_id": new_user.id,
        "email": new_user.email,
        "session_token": create_session_token(new_user),
    }

@router.post("/login")
def login(data: schemas.UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if user and verify_pw(data.password, user.password):
        return {
            "status": "success",
            "user_id": user.id,
            "email": user.email,
            "session_token": create_session_token(user),
        }
    return {"status": "fail", "error": "Invalid credentials"}


@router.post("/session")
def verify_session(data: schemas.SessionRequest, db: Session = Depends(get_db)):
    try:
        payload = verify_session_token(data.token)
    except SignatureExpired:
        return {"status": "fail", "error": "Session expired"}
    except BadSignature:
        return {"status": "fail", "error": "Invalid session"}

    user = db.query(models.User).filter(models.User.id == payload["user_id"]).first()
    if not user:
        return {"status": "fail", "error": "User not found"}

    return {
        "status": "success",
        "user_id": user.id,
        "email": user.email,
    }
