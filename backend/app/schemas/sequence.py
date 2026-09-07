from datetime import date

from pydantic import BaseModel, Field


class SequenceStateResponse(BaseModel):
    """What the client is allowed to know about today's run.

    `digits` only ever contains the current round's prefix, never the
    full daily sequence.
    """

    challenge_id: int
    challenge_date: date
    round: int
    total_rounds: int
    digits: str | None = None
    completed: bool
    score: int | None = None


class SequenceAnswer(BaseModel):
    round: int = Field(ge=1)
    answer: str = Field(max_length=64)


class SequenceAnswerResponse(BaseModel):
    correct: bool
    round: int
    game_over: bool
    score: int | None = None
    next_round: int | None = None
    next_digits: str | None = None
