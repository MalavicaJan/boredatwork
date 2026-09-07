from datetime import datetime, timezone

from app.models.game_result import GameResult
from app.services.wordly import create_daily_challenge


def test_register_user(client):
    response = client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_username(client):
    first_response = client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "another-password",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Username already exists"


def test_login_user(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    response = client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert "session_id" in response.cookies


def test_login_wrong_password(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    response = client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_get_current_user(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    login_response = client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    assert login_response.status_code == 200

    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_logout_user(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    logout_response = client.post("/api/v1/users/logout")

    assert logout_response.status_code == 200

    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_get_user_streak(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    response = client.get("/api/v1/users/streak")

    assert response.status_code == 200

    data = response.json()

    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0


def test_get_daily_progress(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    response = client.get("/api/v1/users/daily-progress")

    assert response.status_code == 200
    assert response.json() == []


def test_daily_progress_after_wordly_completion(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    game_response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "music"},
    )

    assert game_response.status_code == 200
    assert game_response.json()["correct"] is True

    response = client.get("/api/v1/users/daily-progress")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["game"] == "wordly"
    assert data[0]["completed"] is True


def test_streak_after_wordly_completion(client, db_session):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    login_response = client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    assert login_response.status_code == 200

    me_response = client.get("/api/v1/users/me")

    assert me_response.status_code == 200

    challenge = create_daily_challenge(
        db_session,
        datetime.now(timezone.utc).date(),
    )

    game_response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": challenge.word},
    )

    assert game_response.status_code == 200
    assert game_response.json()["correct"] is True

    results = db_session.query(GameResult).all()

    assert len(results) == 1

    response = client.get("/api/v1/users/streak")

    assert response.status_code == 200

    data = response.json()

    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1


def test_get_user_streak_requires_login(client):
    response = client.get("/api/v1/users/streak")

    assert response.status_code == 401