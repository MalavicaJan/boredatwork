from pydantic import BaseModel


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int