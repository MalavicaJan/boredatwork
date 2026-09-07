from datetime import date

from app.services.sequence import create_daily_challenge


def test_sequence_answer_correct(client, db_session):
    challenge = create_daily_challenge(
        db_session,
        date.today(),
    )

    expected = challenge.sequence[:3]

    response = client.post(
        "/api/v1/sequence/answer",
        json={
            "round": 1,
            "answer": expected,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "correct": True,
        "round": 1,
        "game_over": False,
    }


def test_sequence_answer_incorrect(client, db_session):
    challenge = create_daily_challenge(
        db_session,
        date.today(),
    )

    expected = challenge.sequence[:3]

    wrong_answer = "000"
    if wrong_answer == expected:
        wrong_answer = "111"

    response = client.post(
        "/api/v1/sequence/answer",
        json={
            "round": 1,
            "answer": wrong_answer,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "correct": False,
        "round": 1,
        "game_over": True,
        "score": 0,
    }


def test_sequence_answer_invalid_round(client, db_session):
    response = client.post(
        "/api/v1/sequence/answer",
        json={
            "round": 7,
            "answer": "123456789",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid round"


def test_sequence_answer_invalid_length(client, db_session):
    response = client.post(
        "/api/v1/sequence/answer",
        json={
            "round": 2,
            "answer": "123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Answer must be exactly 4 digits"


def test_sequence_round_six_failure_returns_score_five(
    client,
    db_session,
):
    challenge = create_daily_challenge(
        db_session,
        date.today(),
    )

    expected = challenge.sequence[:8]

    wrong_answer = "00000000"
    if wrong_answer == expected:
        wrong_answer = "11111111"

    response = client.post(
        "/api/v1/sequence/answer",
        json={
            "round": 6,
            "answer": wrong_answer,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "correct": False,
        "round": 6,
        "game_over": True,
        "score": 5,
    }