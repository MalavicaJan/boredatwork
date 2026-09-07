import random
from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.game_result import GameResult
from app.models.wordly import WordlyChallenge
from app.models.wordly_guess import WordlyGuess
from app.models.wordly_word import DAILY, PRACTICE, WordlyWord


WORD_LENGTH = 5
MAX_ATTEMPTS = 6
GAME = "wordly"


def get_daily_challenge(
    db: Session,
    challenge_date: date,
) -> WordlyChallenge | None:
    return (
        db.query(WordlyChallenge)
        .filter(WordlyChallenge.challenge_date == challenge_date)
        .first()
    )


def create_daily_challenge(
    db: Session,
    challenge_date: date,
) -> WordlyChallenge:
    existing_challenge = get_daily_challenge(db, challenge_date)

    if existing_challenge:
        return existing_challenge

    words = (
        db.query(WordlyWord)
        .filter(WordlyWord.pool == DAILY)
        .all()
    )

    if not words:
        raise RuntimeError("No Wordly words available")

    challenge = WordlyChallenge(
        challenge_date=challenge_date,
        word=random.choice(words).word,
    )

    db.add(challenge)

    try:
        db.commit()
    except IntegrityError:
        # Another request created today's challenge first.
        db.rollback()

        existing_challenge = get_daily_challenge(db, challenge_date)

        if existing_challenge is None:
            raise

        return existing_challenge

    db.refresh(challenge)

    return challenge


def evaluate_guess(word: str, guess: str) -> list[str]:
    """Wordle-style scoring, in two passes so repeated letters are only
    credited as many times as they actually appear."""
    result = ["absent"] * WORD_LENGTH
    remaining = list(word)

    for index, letter in enumerate(guess):
        if letter == word[index]:
            result[index] = "correct"
            remaining[index] = None

    for index, letter in enumerate(guess):
        if result[index] == "correct":
            continue

        if letter in remaining:
            result[index] = "present"
            remaining[remaining.index(letter)] = None

    return result


def get_guesses(
    db: Session,
    user_id: int,
    challenge_id: int,
) -> list[WordlyGuess]:
    return (
        db.query(WordlyGuess)
        .filter(
            WordlyGuess.user_id == user_id,
            WordlyGuess.challenge_id == challenge_id,
        )
        .order_by(WordlyGuess.id)
        .all()
    )


def get_result(
    db: Session,
    user_id: int,
    challenge_id: int,
) -> GameResult | None:
    return (
        db.query(GameResult)
        .filter(
            GameResult.user_id == user_id,
            GameResult.challenge_id == challenge_id,
            GameResult.game == GAME,
            GameResult.completed.is_(True),
        )
        .first()
    )


def record_result(
    db: Session,
    user_id: int,
    challenge_id: int,
    score: int,
    won: bool,
) -> GameResult:
    """Store the finished game. `won` is explicit rather than derived
    from the score: winning on the sixth guess and losing both score 6.
    """
    result = GameResult(
        user_id=user_id,
        challenge_id=challenge_id,
        game=GAME,
        score=score,
        won=won,
        completed=True,
    )

    db.add(result)

    try:
        db.commit()
    except IntegrityError:
        # Two guesses submitted at once. The first one stands.
        db.rollback()

        existing = get_result(db, user_id, challenge_id)

        if existing is None:
            raise

        return existing

    db.refresh(result)

    return result


def get_practice_word(db: Session, word_id: int) -> WordlyWord | None:
    return (
        db.query(WordlyWord)
        .filter(
            WordlyWord.id == word_id,
            WordlyWord.pool == PRACTICE,
        )
        .first()
    )


def get_random_practice_word(
    db: Session,
    exclude_id: int | None = None,
) -> WordlyWord | None:
    """A word from the practice pool, avoiding the one just played."""
    query = db.query(WordlyWord).filter(WordlyWord.pool == PRACTICE)

    if exclude_id is not None:
        candidate = (
            query.filter(WordlyWord.id != exclude_id)
            .order_by(func.random())
            .first()
        )

        if candidate:
            return candidate

        # Pool of one: repeating beats returning nothing.

    return query.order_by(func.random()).first()
