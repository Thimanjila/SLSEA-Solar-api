from fastapi import APIRouter, Depends, Query, Security
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Province, District, GridSubstation, SolarInstallation, User
from app.schemas.domain import ProvinceOut, DistrictOut, SubstationOut, InstallationOut

router = APIRouter(prefix="/api/v1", tags=["Hierarchy"])

@router.get("/provinces", response_model=list[ProvinceOut])
def provinces(db: Session = Depends(get_db), user: User = Security(get_current_user, scopes=["analyst-read-national"])):
    return db.scalars(select(Province).order_by(Province.name)).all()

@router.get("/provinces/{province_id}/districts", response_model=list[DistrictOut])
def province_districts(province_id: int, db: Session = Depends(get_db), user: User = Security(get_current_user, scopes=["analyst-read-national"])):
    return db.scalars(select(District).where(District.province_id == province_id).order_by(District.name)).all()

@router.get("/districts", response_model=list[DistrictOut])
def districts(db: Session = Depends(get_db), user: User = Security(get_current_user, scopes=["analyst-read-national"])):
    return db.scalars(select(District).order_by(District.name)).all()

@router.get("/districts/{district_id}/grid-substations", response_model=list[SubstationOut])
def district_substations(district_id: int, db: Session = Depends(get_db), user: User = Security(get_current_user, scopes=["analyst-read-national"])):
    return db.scalars(select(GridSubstation).where(GridSubstation.district_id == district_id).order_by(GridSubstation.name)).all()

@router.get("/grid-substations", response_model=list[SubstationOut])
def substations(db: Session = Depends(get_db), user: User = Security(get_current_user, scopes=["analyst-read-national"])):
    return db.scalars(select(GridSubstation).order_by(GridSubstation.name)).all()

@router.get("/grid-substations/{substation_id}/installations", response_model=list[InstallationOut])
def substation_installations(substation_id: int, db: Session = Depends(get_db), user: User = Security(get_current_user, scopes=["analyst-read-national"])):
    return db.scalars(select(SolarInstallation).where(SolarInstallation.substation_id == substation_id).order_by(SolarInstallation.id)).all()
