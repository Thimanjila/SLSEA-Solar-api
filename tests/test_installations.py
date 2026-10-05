from app.core.security import hash_password
from app.models import District, GridSubstation, Province, SolarInstallation, User


def test_get_installation(client, db_session):
    province = Province(name="Test Province")
    db_session.add(province)
    db_session.flush()

    district = District(
        name="Test District",
        province_id=province.id,
    )
    db_session.add(district)
    db_session.flush()

    substation = GridSubstation(
        name="Test Substation",
        district_id=district.id,
    )
    db_session.add(substation)
    db_session.flush()

    installation = SolarInstallation(
        site_name="Test Solar Site",
        meter_id="TEST-METER-001",
        capacity_kw=50.0,
        address="Test Address",
        substation_id=substation.id,
    )
    db_session.add(installation)

    user = User(
        username="test_installation_user",
        password_hash=hash_password("TestPassword123!"),
        role="national_analyst",
    )
    db_session.add(user)

    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_installation_user",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        f"/api/v1/installations/{installation.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == installation.id
    assert body["site_name"] == "Test Solar Site"
    assert body["meter_id"] == "TEST-METER-001"
    assert body["capacity_kw"] == 50.0
    assert body["address"] == "Test Address"
