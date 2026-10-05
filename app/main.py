from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.errors import integrity_exception_handler, validation_exception_handler
from app.db.session import Base, engine
from app.api.routes import auth, hierarchy, installations

app = FastAPI(
    title="SLSEA Real-Time Solar Generation Data API",
    version="1.0.0",
    description="REST API for real-time and historical solar generation data.",
)

Base.metadata.create_all(bind=engine)

app.add_exception_handler(RequestValidationError, validation_exception_handler)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail

    if isinstance(detail, dict) and "code" in detail:
        error = detail
    elif exc.status_code == 401 and str(detail) == "Not authenticated":
        error = {
            "code": "AUTH_REQUIRED",
            "message": "Authentication required",
            "detail": None,
        }
    else:
        error = {
            "code": "HTTP_ERROR",
            "message": str(detail),
            "detail": None,
        }

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error},
        headers=exc.headers or {},
    )

from sqlalchemy.exc import IntegrityError
app.add_exception_handler(IntegrityError, integrity_exception_handler)

@app.get("/health", tags=["Operations"])
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(hierarchy.router)
app.include_router(installations.router)
