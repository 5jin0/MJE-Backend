from enum import Enum


class ActivityType(Enum):
    WALK = "WALK"
    PARK = "PARK"
    MOVIE = "MOVIE"
    EXHIBITION = "EXHIBITION"
    EXPERIENCE = "EXPERIENCE"
    SHOPPING = "SHOPPING"
    NIGHTLIFE = "NIGHTLIFE"

    @property
    def is_nightlife(self) -> bool:
        return self == ActivityType.NIGHTLIFE

    @property
    def title_phrase(self) -> str:
        return {
            ActivityType.WALK: "산책",
            ActivityType.PARK: "공원",
            ActivityType.MOVIE: "영화",
            ActivityType.EXHIBITION: "전시",
            ActivityType.EXPERIENCE: "체험",
            ActivityType.SHOPPING: "쇼핑",
            ActivityType.NIGHTLIFE: "야경",
        }[self]

    @property
    def title_priority(self) -> int:
        return {
            ActivityType.EXHIBITION: 10,
            ActivityType.EXPERIENCE: 9,
            ActivityType.MOVIE: 9,
            ActivityType.WALK: 8,
            ActivityType.SHOPPING: 8,
            ActivityType.NIGHTLIFE: 8,
            ActivityType.PARK: 7,
        }[self]
