from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BlackoutToken(BaseModel):
    kind: Literal["word", "fixed"]
    # Only for fixed tokens: punctuation, whitespace, numbers and the
    # common words that start visible.
    text: str | None = None
    # Only for hidden tokens. Length is the whole hint.
    length: int | None = None


class BlackoutStateResponse(BaseModel):
    challenge_id: int
    challenge_date: date
    title_tokens: list[BlackoutToken]
    body_tokens: list[BlackoutToken]
    # How many hidden words the title has, so the client can tell when
    # it has been uncovered without ever being told what it is.
    title_word_count: int


class BlackoutGuessRequest(BaseModel):
    challenge_id: int
    guess: str = Field(max_length=40)


class BlackoutHit(BaseModel):
    index: int
    # The original text, so casing survives ("napoleon" -> "Napoleon").
    text: str


class BlackoutGuessResponse(BaseModel):
    guess: str
    title_hits: list[BlackoutHit]
    body_hits: list[BlackoutHit]
    count: int


class BlackoutRevealRequest(BaseModel):
    challenge_id: int


class BlackoutRevealResponse(BaseModel):
    title: str
    title_tokens: list[BlackoutToken]
    body_tokens: list[BlackoutToken]
    # Held back until the game ends: the URL contains the title.
    source_url: str
