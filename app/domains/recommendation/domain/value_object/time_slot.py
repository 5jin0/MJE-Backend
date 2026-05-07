from enum import Enum


class TimeSlot(Enum):
    MORNING = "morning"
    LUNCH = "lunch"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    LATE_NIGHT = "late_night"

    @classmethod
    def from_time(cls, time_str: str) -> "TimeSlot":
        h, m = map(int, time_str.split(":"))
        total = h * 60 + m
        if total < 11 * 60 + 30:
            return cls.MORNING
        if total < 14 * 60:
            return cls.LUNCH
        if total < 17 * 60 + 30:
            return cls.AFTERNOON
        if total < 21 * 60 + 30:
            return cls.EVENING
        return cls.LATE_NIGHT

    # 기존 코드 호환
    @classmethod
    def from_start_time(cls, time_str: str) -> "TimeSlot":
        return cls.from_time(time_str)

    @property
    def slot_start_minutes(self) -> int:
        _starts = {
            TimeSlot.MORNING: 9 * 60,
            TimeSlot.LUNCH: 11 * 60 + 30,
            TimeSlot.AFTERNOON: 14 * 60,
            TimeSlot.EVENING: 17 * 60 + 30,
            TimeSlot.LATE_NIGHT: 21 * 60 + 30,
        }
        return _starts[self]

    @property
    def label(self) -> str:
        return {
            TimeSlot.MORNING: "아침",
            TimeSlot.LUNCH: "점심",
            TimeSlot.AFTERNOON: "오후",
            TimeSlot.EVENING: "저녁",
            TimeSlot.LATE_NIGHT: "심야",
        }[self]

    @property
    def time_context(self) -> str:
        return {
            TimeSlot.MORNING: "가볍게 시작하는",
            TimeSlot.LUNCH: "여유롭게 즐기는",
            TimeSlot.AFTERNOON: "오후에 즐기는",
            TimeSlot.EVENING: "저녁에 즐기는",
            TimeSlot.LATE_NIGHT: "심야까지 이어지는",
        }[self]
