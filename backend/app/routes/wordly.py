from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.wordly_guess import WordlyGuess
from app.schemas.wordly import (
    WordlyChallengeResponse,
    WordlyGuessEntry,
    WordlyGuessRequest,
    WordlyGuessResponse,
    WordlyPracticeGuessRequest,
    WordlyPracticeGuessResponse,
    WordlyPracticeRevealRequest,
    WordlyPracticeRevealResponse,
    WordlyPracticeWordResponse,
    WordlyStateResponse,
)
from app.services.wordly import (
    MAX_ATTEMPTS,
    WORD_LENGTH,
    create_daily_challenge,
    evaluate_guess,
    get_guesses,
    get_practice_word,
    get_random_practice_word,
    get_result,
    record_result,
)
from app.session import get_optional_current_user


router = APIRouter(
    prefix="/api/v1/wordly",
    tags=["wordly"],
)


def today() -> date:
    return datetime.now(timezone.utc).date()


@router.get("/today", response_model=WordlyChallengeResponse)
def get_today_wordly(
    db: Session = Depends(get_db),
):
    return create_daily_challenge(db, today())


@router.post("/guess", response_model=WordlyGuessResponse)
def submit_wordly_guess(
    submission: WordlyGuessRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    challenge = create_daily_challenge(db, today())

    guess = submission.guess.strip().lower()

    if len(guess) != WORD_LENGTH or not guess.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guess must be exactly {WORD_LENGTH} letters",
        )

    result = evaluate_guess(challenge.word, guess)
    correct = guess == challenge.word

    # Anonymous play is not stored, so the server has no attempt count
    # to enforce and never reveals the word. The client caps the board
    # at six rows; a refresh starts over, which costs nothing because
    # nothing was being kept.
    if not current_user:
        return WordlyGuessResponse(
            correct=correct,
            result=result,
            game_over=correct,
            won=correct,
        )

    if get_result(db, current_user.id, challenge.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already completed today's Wordly",
        )

    attempts_used = len(get_guesses(db, current_user.id, challenge.id)) + 1

    db.add(
        WordlyGuess(
            user_id=current_user.id,
            challenge_id=challenge.id,
            guess=guess,
        )
    )
    db.commit()

    out_of_guesses = attempts_used >= MAX_ATTEMPTS
    game_over = correct or out_of_guesses

    if game_over:
        record_result(
            db,
            current_user.id,
            challenge.id,
            score=attempts_used,
            won=correct,
        )

    return WordlyGuessResponse(
        correct=correct,
        result=result,
        game_over=game_over,
        won=correct,
        attempts_used=attempts_used,
        attempts_remaining=max(0, MAX_ATTEMPTS - attempts_used),
        # Only on a loss: a winner already knows the word.
        answer=challenge.word if game_over and not correct else None,
    )


@router.get("/state", response_model=WordlyStateResponse)
def get_wordly_state(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    challenge = create_daily_challenge(db, today())

    if not current_user:
        return WordlyStateResponse(
            challenge_id=challenge.id,
            challenge_date=challenge.challenge_date,
            guesses=[],
            attempts_used=0,
            attempts_remaining=MAX_ATTEMPTS,
            completed=False,
            won=False,
        )

    guesses = get_guesses(db, current_user.id, challenge.id)
    result = get_result(db, current_user.id, challenge.id)

    completed = result is not None
    won = result.won if result else False

    return WordlyStateResponse(
        challenge_id=challenge.id,
        challenge_date=challenge.challenge_date,
        guesses=[
            WordlyGuessEntry(
                guess=guess.guess,
                result=evaluate_guess(challenge.word, guess.guess),
            )
            for guess in guesses
        ],
        attempts_used=len(guesses),
        attempts_remaining=max(0, MAX_ATTEMPTS - len(guesses)),
        completed=completed,
        won=won,
        answer=challenge.word if completed and not won else None,
    )


# --- Practice mode -------------------------------------------------
#
# No daily gate, no account, nothing stored, same for everyone. The word
# is disposable rather than secret, so the server will simply tell you
# what it was when you ask. Practice draws from its own pool so that
# hammering these endpoints reveals nothing about the daily answer.


def load_practice_word_or_404(db: Session, word_id: int):
    word = get_practice_word(db, word_id)

    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice word not found",
        )

    return word


@router.get("/practice/new", response_model=WordlyPracticeWordResponse)
def get_practice_word_handle(
    exclude: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    word = get_random_practice_word(db, exclude)

    if not word:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No practice words available yet",
        )

    return WordlyPracticeWordResponse(
        word_id=word.id,
        word_length=WORD_LENGTH,
        max_attempts=MAX_ATTEMPTS,
    )


@router.post("/practice/guess", response_model=WordlyPracticeGuessResponse)
def submit_practice_guess(
    submission: WordlyPracticeGuessRequest,
    db: Session = Depends(get_db),
):
    word = load_practice_word_or_404(db, submission.word_id)

    guess = submission.guess.strip().lower()

    if len(guess) != WORD_LENGTH or not guess.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guess must be exactly {WORD_LENGTH} letters",
        )

    return WordlyPracticeGuessResponse(
        correct=guess == word.word,
        result=evaluate_guess(word.word, guess),
    )


@router.post("/practice/reveal", response_model=WordlyPracticeRevealResponse)
def reveal_practice_word(
    submission: WordlyPracticeRevealRequest,
    db: Session = Depends(get_db),
):
    word = load_practice_word_or_404(db, submission.word_id)

    return WordlyPracticeRevealResponse(answer=word.word)
