from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.modules.authentication.models import User
from app.modules.authentication.repository import get_user_by_id

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload.")

    user = get_user_by_id(db, user_id)
    if not user:
        raise AuthenticationError("User not found.")
    if not user.is_active:
        raise AuthenticationError("Account is deactivated.")
    return user
