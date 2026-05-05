from dataclasses import dataclass


@dataclass(frozen=True)
class PlaceSchedule:
    start_time: str
    end_time: str
    duration_minutes: int
    move_time_to_next_minutes: int
