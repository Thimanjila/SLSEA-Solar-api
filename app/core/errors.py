from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

def error_body(code, message, detail=None):
    return {"error": {"code": code, "message": message, "detail": detail}}

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content=error_body("VALIDATION_ERROR", "Request validation failed", str(exc)))

async def integrity_exception_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=400, content=error_body("INTEGRITY_ERROR", "Request conflicts with stored data", str(exc.orig)))
