from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(pw: str):
    return pwd_context.hash(pw[:72])

def verify_pw(pw: str, hashed: str):
    try:
        return pwd_context.verify(pw[:72], hashed)
    except:
        return False

@router.post("/signup")
def signup(data: schemas.UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == data.email).first()
    if db_user:
        return {"status": "fail", "error": "User exists"}
    
    new_user = models.User(email=data.email, password=hash_pw(data.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id}

@router.post("/login")
def login(data: schemas.UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if user and verify_pw(data.password, user.password):
        return {"status": "success", "user_id": user.id}
    return {"status": "fail", "error": "Invalid credentials"}
