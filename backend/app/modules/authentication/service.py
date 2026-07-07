from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, UserAlreadyExistsError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.authentication import repository
from app.modules.authentication.models import User
from app.modules.authentication.schemas import LoginRequest, RegisterRequest


def register_user(db: Session, data: RegisterRequest) -> tuple[User, str]:
    existing = repository.get_user_by_email(db, data.email)
    if existing:
        raise UserAlreadyExistsError(data.email)

    hashed = hash_password(data.password)
    user = repository.create_user(db, data.email, data.full_name, hashed)
    token = create_access_token({"sub": user.id, "email": user.email})
    return user, token


def authenticate_user(db: Session, data: LoginRequest) -> tuple[User, str]:
    user = repository.get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")
    if not user.is_active:
        raise AuthenticationError("Account is deactivated.")

    token = create_access_token({"sub": user.id, "email": user.email})
    return user, token
