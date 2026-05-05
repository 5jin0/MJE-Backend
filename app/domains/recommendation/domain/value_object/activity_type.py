from enum import Enum


class ActivityType(Enum):
    CORE_ACTIVITY = "CORE_ACTIVITY"
    SUB_ACTIVITY = "SUB_ACTIVITY"


class ActivityKind(Enum):
    # CORE_ACTIVITY — 기본 추천에 우선 사용  (value, activity_type, duration_minutes)
    EXHIBITION  = ("EXHIBITION",  ActivityType.CORE_ACTIVITY, 90)
    WALK        = ("WALK",        ActivityType.CORE_ACTIVITY, 90)
    SHOPPING    = ("SHOPPING",    ActivityType.CORE_ACTIVITY, 90)
    POPUP       = ("POPUP",       ActivityType.CORE_ACTIVITY, 90)
    WORKSHOP    = ("WORKSHOP",    ActivityType.CORE_ACTIVITY, 120)
    INDOOR_PLAY = ("INDOOR_PLAY", ActivityType.CORE_ACTIVITY, 120)

    # SUB_ACTIVITY — 시간대/코스 흐름에 따라 보조 사용
    MOVIE      = ("MOVIE",       ActivityType.SUB_ACTIVITY, 120)
    KARAOKE    = ("KARAOKE",     ActivityType.SUB_ACTIVITY, 120)
    BAR        = ("BAR",         ActivityType.SUB_ACTIVITY, 150)
    NIGHT_VIEW = ("NIGHT_VIEW",  ActivityType.SUB_ACTIVITY, 90)
    SPORTS     = ("SPORTS",      ActivityType.SUB_ACTIVITY, 120)
    LATE_NIGHT = ("LATE_NIGHT",  ActivityType.SUB_ACTIVITY, 150)

    def __new__(cls, value: str, activity_type: ActivityType, duration_minutes: int) -> "ActivityKind":
        obj = object.__new__(cls)
        obj._value_ = value
        obj._activity_type = activity_type
        obj._duration_minutes = duration_minutes
        return obj

    @property
    def activity_type(self) -> ActivityType:
        return self._activity_type

    @property
    def duration_minutes(self) -> int:
        return self._duration_minutes

    @property
    def is_core(self) -> bool:
        return self._activity_type == ActivityType.CORE_ACTIVITY

    @classmethod
    def core_activities(cls) -> list["ActivityKind"]:
        return [a for a in cls if a.activity_type == ActivityType.CORE_ACTIVITY]

    @classmethod
    def sub_activities(cls) -> list["ActivityKind"]:
        return [a for a in cls if a.activity_type == ActivityType.SUB_ACTIVITY]
