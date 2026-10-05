from app.core.security import hash_password
from app.models import User


def test_login_returns_access_token(client, db_session):
    user = User(
        username="test_national_analyst",
        password_hash=hash_password("TestPassword123!"),
        role="national_analyst",
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_national_analyst",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_login_rejects_wrong_password(client, db_session):
    user = User(
        username="test_wrong_password",
        password_hash=hash_password("CorrectPassword123!"),
        role="national_analyst",
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_wrong_password",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
