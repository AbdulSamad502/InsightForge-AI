from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.modules.authentication import service
from app.modules.authentication.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse
)
from app.core.database import get_db
from app.shared.dependencies import get_current_user
from app.modules.authentication.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user, token = service.register_user(db, data)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user, token = service.authenticate_user(db, data)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)