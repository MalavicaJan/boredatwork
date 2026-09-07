from datetime import date

from app.services.streak import (
    calculate_current_streak,
    calculate_longest_streak,
)


def test_current_streak():
    completed_dates = {
        date(2026, 9, 1),
        date(2026, 9, 2),
        date(2026, 9, 3),
    }

    assert calculate_current_streak(
        completed_dates,
        date(2026, 9, 3),
    ) == 3


def test_current_streak_is_zero_when_today_is_missing():
    completed_dates = {
        date(2026, 9, 1),
        date(2026, 9, 2),
    }

    assert calculate_current_streak(
        completed_dates,
        date(2026, 9, 3),
    ) == 0


def test_longest_streak():
    completed_dates = {
        date(2026, 9, 1),
        date(2026, 9, 2),
        date(2026, 9, 4),
        date(2026, 9, 5),
        date(2026, 9, 6),
    }

    assert calculate_longest_streak(completed_dates) == 3