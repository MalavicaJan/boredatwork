from datetime import date

from app.models.sequence import SequenceChallenge
from app.services.sequence import create_daily_challenge, get_daily_challenge


def test_create_daily_sequence_challenge(db_session):
    challenge_date = date(2026, 9, 3)

    challenge = create_daily_challenge(
        db_session,
        challenge_date,
    )

    assert challenge.challenge_date == challenge_date
    assert len(challenge.sequence) == 20
    assert challenge.sequence.isdigit()


def test_daily_sequence_challenge_is_reused(db_session):
    challenge_date = date(2026, 9, 3)

    first = create_daily_challenge(
        db_session,
        challenge_date,
    )

    second = create_daily_challenge(
        db_session,
        challenge_date,
    )

    assert first.id == second.id
    assert first.sequence == second.sequence


def test_daily_sequence_challenge_can_be_loaded(db_session):
    challenge_date = date(2026, 9, 3)

    created = create_daily_challenge(
        db_session,
        challenge_date,
    )

    loaded = get_daily_challenge(
        db_session,
        challenge_date,
    )

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.sequence == created.sequence