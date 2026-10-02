from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import create_access_token, verify_password
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/token")
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from app.models import User
    user = db.scalar(select(User).where(User.username == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password", "detail": None},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(user), "token_type": "bearer"}
