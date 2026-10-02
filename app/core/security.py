from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models import User

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scopes={
        "installation-write": "A solar installation may submit readings for itself",
        "analyst-read-national": "Read national data",
        "analyst-read-district": "Read data within the user's district",
    },
)

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(user: User) -> str:
    scopes = []
    if user.role == "device":
        scopes = ["installation-write"]
    elif user.role == "national_analyst":
        scopes = ["analyst-read-national"]
    elif user.role == "district_analyst":
        scopes = ["analyst-read-district"]
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "district_id": user.district_id,
        "installation_id": user.installation_id,
        "scope": " ".join(scopes),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "AUTH_REQUIRED", "message": "Authentication required", "detail": None},
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub", "0"))
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception
    user = db.get(User, user_id)
    if not user:
        raise credentials_exception
    token_scopes = set(payload.get("scope", "").split())
    if not set(security_scopes.scopes).issubset(token_scopes):
        raise HTTPException(
            status_code=403,
            detail={"code": "INSUFFICIENT_SCOPE", "message": "Insufficient scope", "detail": None},
        )
    return user
