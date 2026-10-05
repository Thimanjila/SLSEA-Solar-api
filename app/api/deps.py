
from fastapi import Depends, HTTPException, Security

from app.core.security import get_current_user
from app.models import User


def require_analyst(
    user: User = Security(get_current_user),
) -> User:
    """
    Allow only national and district analysts to access read endpoints.
    """
    if user.role not in {"national_analyst", "district_analyst"}:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ANALYST_ACCESS_REQUIRED",
                "message": "Analyst access is required",
                "detail": "Only national and district analysts may access read endpoints.",
            },
        )

    return user


def require_device_for_installation(user: User, installation_id: int):
    """
    Allow a device to submit readings only for its own installation.
    """
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
    """
    Enforce jurisdiction-scoped read access.

    National analysts can read all districts.
    District analysts can read only their assigned district.
    """
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
