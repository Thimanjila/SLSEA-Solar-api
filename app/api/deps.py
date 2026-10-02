from fastapi import HTTPException
from app.models import User

def require_device_for_installation(user: User, installation_id: int):
    if user.role != "device" or user.installation_id != installation_id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "INSTALLATION_SCOPE_DENIED",
                "message": "Device is not authorised for this installation",
                "detail": "A device may only submit readings for its own installation.",
            },
        )

def require_read_access(user: User, district_id: int):
    if user.role == "national_analyst":
        return
    if user.role == "district_analyst" and user.district_id == district_id:
        return
    raise HTTPException(
        status_code=403,
        detail={
            "code": "JURISDICTION_SCOPE_DENIED",
            "message": "The requested resource is outside your jurisdiction",
            "detail": "District analysts may only read their assigned district.",
        },
    )
