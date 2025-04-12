from fastapi import Depends, HTTPException, status
from .database import get_db
from .models import User
from .schemas import UserCreate, UserLogin, UserOut
import hashlib
from sqlalchemy.orm import Session

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    db_user = User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email, 
                                   User.password == hash_password(user.password)).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return db_user

# Router setup (if needed separately)
from fastapi import APIRouter
router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(user, db)

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = authenticate_user(user, db)
    return {"message": "Login successful", "user_id": authenticated_user.id}