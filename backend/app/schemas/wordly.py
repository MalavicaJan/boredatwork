from datetime import date

from pydantic import BaseModel, Field


class WordlyGuessRequest(BaseModel):
    guess: str = Field(max_length=32)


class WordlyGuessEntry(BaseModel):
    guess: str
    result: list[str]


class WordlyGuessResponse(BaseModel):
    correct: bool
    result: list[str]
    game_over: bool
    won: bool = False
    # Null for anonymous players: nothing is stored for them, so the
    # server has no attempt count to report.
    attempts_used: int | None = None
    attempts_remaining: int | None = None
    answer: str | None = None


class WordlyStateResponse(BaseModel):
    challenge_id: int
    challenge_date: date
    guesses: list[WordlyGuessEntry]
    attempts_used: int
    attempts_remaining: int
    completed: bool
    won: bool
    # Only present once a logged-in player has finished and lost, so a
    # reload still shows them the word.
    answer: str | None = None


class WordlyChallengeResponse(BaseModel):
    id: int
    challenge_date: date

    model_config = {
        "from_attributes": True
    }


class WordlyPracticeWordResponse(BaseModel):
    """A handle on a practice word. The word itself stays server-side
    until the player asks to be told."""

    word_id: int
    word_length: int
    max_attempts: int


class WordlyPracticeGuessRequest(BaseModel):
    word_id: int
    guess: str = Field(max_length=32)


class WordlyPracticeGuessResponse(BaseModel):
    correct: bool
    result: list[str]


class WordlyPracticeRevealRequest(BaseModel):
    word_id: int


class WordlyPracticeRevealResponse(BaseModel):
    answer: str
