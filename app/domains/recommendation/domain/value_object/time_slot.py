from enum import Enum


class TimeSlot(Enum):
    LUNCH = "LUNCH"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    NIGHT = "NIGHT"

    @classmethod
    def from_start_time(cls, time_str: str) -> "TimeSlot":
        hour, _ = map(int, time_str.split(":"))
        if hour < 14:
            return cls.LUNCH
        if hour < 18:
            return cls.AFTERNOON
        if hour < 21:
            return cls.EVENING
        return cls.NIGHT
