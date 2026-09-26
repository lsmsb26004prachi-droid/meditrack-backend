from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth_schemas import Token, UserLogin, UserPublic, UserRegister, UserProfileUpdate
from database import get_db
from dependencies import get_current_user
from models import User
from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserPublic, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        )
    user = User(
        full_name=data.full_name,
        email=email,
        role=data.role,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user, from_attributes=True)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return Token(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=UserPublic)
def read_me(user: User = Depends(get_current_user)):
    return UserPublic.model_validate(user, from_attributes=True)


@router.patch("/profile", response_model=UserPublic)
def update_profile(
    data: UserProfileUpdate, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    if data.date_of_birth is not None:
        user.date_of_birth = data.date_of_birth
    if data.sex is not None:
        user.sex = data.sex
    if data.height_cm is not None:
        user.height_cm = data.height_cm
    if data.weight_kg is not None:
        user.weight_kg = data.weight_kg

    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user, from_attributes=True)