from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import verify_password, get_password_hash, create_access_token, generate_validation_code
import models, schemas

router = APIRouter()

@router.post("/register", response_model=dict, status_code=201)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    # Check duplicates
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.User).filter(models.User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    code = generate_validation_code()
    user = models.User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        validation_code=code,
        is_verified=False,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "validation_code": code,  # In production: send via email
        "user_id": user.id
    }

@router.post("/verify", response_model=dict)
def verify_account(data: schemas.UserVerify, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"message": "Account already verified"}
    if user.validation_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid validation code")

    user.is_verified = True
    db.commit()
    return {"message": "Account verified successfully"}

@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        (models.User.email == credentials.email) |
        (models.User.username == credentials.email)
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin})
    return schemas.Token(
        access_token=token,
        token_type="bearer",
        user=schemas.UserOut.model_validate(user)
    )
