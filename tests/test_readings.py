from datetime import datetime, timezone

from app.core.security import hash_password
from app.models import (
    District,
    GenerationReading,
    GridSubstation,
    Province,
    SolarInstallation,
    User,
)


def test_readings_pagination_and_sorting(client, db_session):
    province = Province(name="Reading Test Province")
    db_session.add(province)
    db_session.flush()

    district = District(
        name="Reading Test District",
        province_id=province.id,
    )
    db_session.add(district)
    db_session.flush()

    substation = GridSubstation(
        name="Reading Test Substation",
        district_id=district.id,
    )
    db_session.add(substation)
    db_session.flush()

    installation = SolarInstallation(
        site_name="Reading Test Site",
        meter_id="READING-METER-001",
        capacity_kw=25.0,
        address="Reading Test Address",
        substation_id=substation.id,
    )
    db_session.add(installation)
    db_session.flush()

    user = User(
        username="reading_test_user",
        password_hash=hash_password("TestPassword123!"),
        role="national_analyst",
    )
    db_session.add(user)
    db_session.flush()

    readings = [
        GenerationReading(
            installation_id=installation.id,
            timestamp=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
            power_kw=10.0,
            cumulative_energy_kwh=100.0,
            voltage=230.0,
        ),
        GenerationReading(
            installation_id=installation.id,
            timestamp=datetime(2026, 10, 1, 11, 0, tzinfo=timezone.utc),
            power_kw=12.0,
            cumulative_energy_kwh=112.0,
            voltage=231.0,
        ),
        GenerationReading(
            installation_id=installation.id,
            timestamp=datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc),
            power_kw=15.0,
            cumulative_energy_kwh=127.0,
            voltage=232.0,
        ),
    ]

    db_session.add_all(readings)
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "reading_test_user",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        f"/api/v1/installations/{installation.id}/readings",
        params={
            "limit": 2,
            "offset": 0,
            "sort": "desc",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["meta"]["total"] == 3
    assert body["meta"]["limit"] == 2
    assert body["meta"]["offset"] == 0
    assert body["meta"]["next"] is not None
    assert body["meta"]["previous"] is None

    assert len(body["data"]) == 2

    assert body["data"][0]["power_kw"] == 15.0
    assert body["data"][1]["power_kw"] == 12.0
