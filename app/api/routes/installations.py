from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, Security

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    require_analyst,
    require_device_for_installation,
    require_read_access,
)
from app.core.headers import apply_cache_headers, is_not_modified, make_etag

from app.db.session import get_db
from app.models import (
    District,
    GenerationReading,
    GridSubstation,
    Province,
    SolarInstallation,
    User,
)
from app.schemas.domain import (
    DistrictOut,
    GenerationSummary,
    InstallationComposite,
    InstallationOut,
    PageMeta,
    ReadingCreate,
    ReadingOut,
    ReadingPage,
    ProvinceOut,
    SubstationOut,
)

router = APIRouter(prefix="/api/v1", tags=["Installations"])


def installation_with_scope(db, installation_id: int, user: User):
    inst = db.get(SolarInstallation, installation_id)

    if not inst:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": "Installation not found",
                "detail": None,
            },
        )

    district_id = db.scalar(
        select(District.id)
        .join(
            GridSubstation,
            GridSubstation.district_id == District.id,
        )
        .where(GridSubstation.id == inst.substation_id)
    )

    require_read_access(user, district_id)

    return inst


@router.get("/installations", response_model=list[InstallationOut])
def list_installations(
    province_id: int | None = Query(None),
    district_id: int | None = Query(None),
    substation_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_analyst),
):
    stmt = select(SolarInstallation)

    # Filter directly by substation without needing a JOIN.
    if substation_id is not None:
        stmt = stmt.where(
            SolarInstallation.substation_id == substation_id
        )

    # Join GridSubstation only once when either district or province
    # filtering is required.
    if district_id is not None or province_id is not None:
        stmt = stmt.join(GridSubstation)

    if district_id is not None:
        stmt = stmt.where(
            GridSubstation.district_id == district_id
        )

    if province_id is not None:
        stmt = stmt.join(District).where(
            District.province_id == province_id
        )

    return db.scalars(
        stmt.order_by(SolarInstallation.id)
    ).all()


@router.get(
    "/installations/{installation_id}",
    response_model=InstallationOut,
)
def get_installation(
    installation_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_analyst),
):
    inst = installation_with_scope(
        db,
        installation_id,
        user,
    )

    etag = make_etag(
        f"installation:{inst.id}:{inst.site_name}:"
        f"{inst.capacity_kw}:{inst.address}"
    )

    last_modified = datetime.now(timezone.utc)

    apply_cache_headers(
        response,
        etag,
        last_modified,
    )

    if is_not_modified(
        request,
        etag,
        last_modified,
    ):
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Last-Modified": response.headers["Last-Modified"],
            },
        )

    return inst


@router.get(
    "/installations/{installation_id}/composite",
    response_model=InstallationComposite,
)
def composite(
    installation_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_analyst),
):
    inst = installation_with_scope(
        db,
        installation_id,
        user,
    )

    sub = db.get(
        GridSubstation,
        inst.substation_id,
    )

    district = db.get(
        District,
        sub.district_id,
    )

    province = db.get(
        Province,
        district.province_id,
    )

    latest = db.scalar(
        select(GenerationReading)
        .where(
            GenerationReading.installation_id == inst.id
        )
        .order_by(
            GenerationReading.timestamp.desc()
        )
        .limit(1)
    )

    etag = make_etag(
        f"composite:{inst.id}:"
        f"{latest.id if latest else 'none'}"
    )

    last_modified = (
        latest.timestamp
        if latest
        else datetime.now(timezone.utc)
    )

    apply_cache_headers(
        response,
        etag,
        last_modified,
    )

    if is_not_modified(
        request,
        etag,
        last_modified,
    ):
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Last-Modified": response.headers["Last-Modified"],
            },
        )

    return InstallationComposite(
        installation=inst,
        substation=SubstationOut.model_validate(sub),
        district=DistrictOut.model_validate(district),
        province=ProvinceOut.model_validate(province),
        last_known_reading=(
            ReadingOut.model_validate(latest)
            if latest
            else None
        ),
    )


@router.get(
    "/installations/{installation_id}/last-known-reading",
    response_model=ReadingOut,
)
def last_known(
    installation_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_analyst),
):
    installation_with_scope(
        db,
        installation_id,
        user,
    )

    latest = db.scalar(
        select(GenerationReading)
        .where(
            GenerationReading.installation_id == installation_id
        )
        .order_by(
            GenerationReading.timestamp.desc()
        )
        .limit(1)
    )

    if not latest:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NO_READING",
                "message": (
                    "No generation reading exists "
                    "for this installation"
                ),
                "detail": None,
            },
        )

    etag = make_etag(
        f"reading:{latest.id}:{latest.timestamp}:"
        f"{latest.power_kw}:{latest.cumulative_energy_kwh}:"
        f"{latest.voltage}"
    )

    apply_cache_headers(
        response,
        etag,
        latest.timestamp,
    )

    if is_not_modified(
        request,
        etag,
        latest.timestamp,
    ):
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Last-Modified": response.headers["Last-Modified"],
            },
        )

    return latest


@router.get(
    "/installations/{installation_id}/readings",
    response_model=ReadingPage,
    responses={
        401: {
            "description": "Authentication required",
        },
        403: {
            "description": "Forbidden - insufficient scope or outside jurisdiction",
        },
        404: {
            "description": "Installation not found",
        },
        422: {
            "description": "Validation error",
        },
    },
)
def readings(
    installation_id: int,
    response: Response,
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    sort: str = Query(
        "desc",
        pattern="^(asc|desc)$",
    ),
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    province_id: int | None = None,
    district_id: int | None = None,
    substation_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_analyst),
):
    inst = installation_with_scope(
        db,
        installation_id,
        user,
    )

    stmt = select(GenerationReading).where(
        GenerationReading.installation_id == installation_id
    )

    if from_time:
        stmt = stmt.where(
            GenerationReading.timestamp >= from_time
        )

    if to_time:
        stmt = stmt.where(
            GenerationReading.timestamp <= to_time
        )

    if (
        province_id is not None
        or district_id is not None
        or substation_id is not None
    ):
        stmt = (
            stmt
            .join(SolarInstallation)
            .join(GridSubstation)
            .join(District)
        )

        if province_id is not None:
            stmt = stmt.where(
                District.province_id == province_id
            )

        if district_id is not None:
            stmt = stmt.where(
                GridSubstation.district_id == district_id
            )

        if substation_id is not None:
            stmt = stmt.where(
                SolarInstallation.substation_id == substation_id
            )

    total = db.scalar(
        select(func.count())
        .select_from(stmt.subquery())
    )

    order = (
        GenerationReading.timestamp.asc()
        if sort == "asc"
        else GenerationReading.timestamp.desc()
    )

    rows = db.scalars(
        stmt
        .order_by(order)
        .offset(offset)
        .limit(limit)
    ).all()

    next_link = (
        f"/api/v1/installations/{installation_id}/readings"
        f"?limit={limit}"
        f"&offset={offset + limit}"
        f"&sort={sort}"
        if offset + limit < total
        else None
    )

    previous_link = (
        f"/api/v1/installations/{installation_id}/readings"
        f"?limit={limit}"
        f"&offset={max(0, offset - limit)}"
        f"&sort={sort}"
        if offset > 0
        else None
    )

    return ReadingPage(
        data=rows,
        meta=PageMeta(
            total=total,
            limit=limit,
            offset=offset,
            next=next_link,
            previous=previous_link,
        ),
    )


@router.post(
    "/installations/{installation_id}/readings",
    response_model=ReadingOut,
    status_code=201,
)
def create_reading(
    installation_id: int,
    payload: ReadingCreate,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Security(
        get_current_user,
        scopes=["installation-write"],
    ),
):
    inst = db.get(
        SolarInstallation,
        installation_id,
    )

    if not inst:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": "Installation not found",
                "detail": None,
            },
        )

    require_device_for_installation(
        user,
        installation_id,
    )

    reading = GenerationReading(
        installation_id=installation_id,
        **payload.model_dump(),
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    response.headers["Location"] = (
        f"/api/v1/installations/"
        f"{installation_id}/readings/"
        f"{reading.id}"
    )

    return reading


@router.get(
    "/installations/{installation_id}/readings/{reading_id}",
    response_model=ReadingOut,
)
def get_reading(
    installation_id: int,
    reading_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(require_analyst),
):
    installation_with_scope(
        db,
        installation_id,
        user,
    )

    reading = db.scalar(
        select(GenerationReading).where(
            GenerationReading.id == reading_id,
            GenerationReading.installation_id == installation_id,
        )
    )

    if not reading:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": "Reading not found",
                "detail": None,
            },
        )

    etag = make_etag(
        f"reading:{reading.id}:{reading.timestamp}:"
        f"{reading.power_kw}:{reading.cumulative_energy_kwh}:"
        f"{reading.voltage}"
    )

    apply_cache_headers(
        response,
        etag,
        reading.timestamp,
    )

    if is_not_modified(
        request,
        etag,
        reading.timestamp,
    ):
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Last-Modified": response.headers["Last-Modified"],
            },
        )

    return reading


@router.get(
    "/districts/{district_id}/generation-summary",
    response_model=GenerationSummary,
)
def district_summary(
    district_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_analyst),
):
    district = db.get(
        District,
        district_id,
    )

    if not district:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": "District not found",
                "detail": None,
            },
        )

    require_read_access(
        user,
        district_id,
    )

    installation_count = db.scalar(
        select(func.count(SolarInstallation.id))
        .join(GridSubstation)
        .where(
            GridSubstation.district_id == district_id
        )
    )

    latest_subq = (
        select(
            GenerationReading.installation_id,
            func.max(
                GenerationReading.timestamp
            ).label("max_ts"),
        )
        .group_by(
            GenerationReading.installation_id
        )
        .subquery()
    )

    current_total = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    GenerationReading.power_kw
                ),
                0.0,
            )
        )
        .join(SolarInstallation)
        .join(GridSubstation)
        .join(
            latest_subq,
            (
                latest_subq.c.installation_id
                == GenerationReading.installation_id
            )
            & (
                latest_subq.c.max_ts
                == GenerationReading.timestamp
            ),
        )
        .where(
            GridSubstation.district_id == district_id
        )
    ) or 0.0

    # Cumulative energy is reported as the latest
    # daily cumulative value per installation.
    from datetime import datetime, timezone

    today_start = datetime.now(
        timezone.utc
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    daily_rows = db.execute(
        select(
            GenerationReading.installation_id,
            func.min(
                GenerationReading.cumulative_energy_kwh
            ).label("first_energy"),
            func.max(
                GenerationReading.cumulative_energy_kwh
            ).label("last_energy"),
        )
        .join(SolarInstallation)
        .join(GridSubstation)
        .where(
            GridSubstation.district_id == district_id,
            GenerationReading.timestamp >= today_start,
        )
        .group_by(
            GenerationReading.installation_id
        )
    ).all()

    today_energy = sum(
        float(
            r.last_energy - r.first_energy
        )
        for r in daily_rows
    )

    reading_count = db.scalar(
        select(func.count(GenerationReading.id))
        .join(SolarInstallation)
        .join(GridSubstation)
        .where(
            GridSubstation.district_id == district_id,
            GenerationReading.timestamp >= today_start,
        )
    ) or 0

    return GenerationSummary(
        district_id=district.id,
        district_name=district.name,
        current_total_power_kw=round(
            float(current_total),
            3,
        ),
        today_total_energy_kwh=round(
            float(today_energy),
            3,
        ),
        installation_count=installation_count or 0,
        reading_count_today=reading_count,
    )