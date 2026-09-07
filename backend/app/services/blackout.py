import random
import re
from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.blackout import BlackoutArticle, BlackoutChallenge


# Every word is hidden, including "the" and "of". Revealing common
# words makes the text readable at a glance, which gives away sentence
# structure and most of the difficulty with it.

# Words, numbers, whitespace, everything else. Kept as one pattern so
# joining the tokens reproduces the original text exactly.
TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*|\d+|\s+|[^\sA-Za-z\d]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def is_guessable(token: str) -> bool:
    """Every alphabetic word is hidden.

    Numbers and punctuation stay visible. Dates and commas give shape to
    the page without giving away vocabulary, and blanking them out adds
    tedium rather than difficulty. Drop the isalpha check here if you
    want numbers hidden too.
    """
    return token[:1].isalpha()


def normalize(token: str) -> str:
    return token.lower()


def redact(text: str) -> list[dict]:
    """Turn text into tokens the client can render.

    Hidden tokens carry only their length. The word itself never leaves
    the server until it is guessed.
    """
    tokens = []

    for token in tokenize(text):
        if is_guessable(token):
            tokens.append({"kind": "word", "length": len(token)})
        else:
            tokens.append({"kind": "fixed", "text": token})

    return tokens


def find_hits(text: str, guess: str) -> list[dict]:
    """Positions where a guessed word appears, with its original casing."""
    target = normalize(guess)

    return [
        {"index": index, "text": token}
        for index, token in enumerate(tokenize(text))
        if is_guessable(token) and normalize(token) == target
    ]


def title_word_count(title: str) -> int:
    """How many hidden words the title has. The client uses this to
    decide whether the puzzle is solved, so it never has to ask the
    server what the answer is."""
    return sum(1 for token in tokenize(title) if is_guessable(token))


def get_article(db: Session, article_id: int) -> BlackoutArticle | None:
    return (
        db.query(BlackoutArticle)
        .filter(BlackoutArticle.id == article_id)
        .first()
    )


def get_daily_challenge(
    db: Session,
    challenge_date: date,
) -> BlackoutChallenge | None:
    return (
        db.query(BlackoutChallenge)
        .filter(BlackoutChallenge.challenge_date == challenge_date)
        .first()
    )


def used_article_ids(db: Session) -> set[int]:
    return {
        row[0]
        for row in db.query(BlackoutChallenge.article_id).all()
    }


def pick_article(db: Session) -> BlackoutArticle | None:
    """Prefer an article that hasn't been used as a daily yet."""
    used = used_article_ids(db)

    query = db.query(BlackoutArticle)

    if used:
        unused = query.filter(~BlackoutArticle.id.in_(used))

        candidate = unused.order_by(func.random()).first()

        if candidate:
            return candidate

        # Whole pool has been used; start repeating.

    return query.order_by(func.random()).first()


def create_daily_challenge(
    db: Session,
    challenge_date: date,
) -> BlackoutChallenge | None:
    existing = get_daily_challenge(db, challenge_date)

    if existing:
        return existing

    article = pick_article(db)

    if not article:
        return None

    challenge = BlackoutChallenge(
        challenge_date=challenge_date,
        article_id=article.id,
    )

    db.add(challenge)

    try:
        db.commit()
    except IntegrityError:
        # Another request created today's challenge first.
        db.rollback()

        existing = get_daily_challenge(db, challenge_date)

        if existing is None:
            raise

        return existing

    db.refresh(challenge)

    return challenge
