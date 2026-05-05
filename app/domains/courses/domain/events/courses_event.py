from dataclasses import dataclass
from enum import Enum


class CoursesEventType(Enum):
    COURSE_CREATE = "course_create"
    CARD_CLICK = "card_click"
    TRYAGAIN_CLICK = "tryagain_click"
    OPTIONCARD_CLICK = "optioncard_click"
    RETURN_CLICK = "return_click"

    @classmethod
    def allowed_values(cls) -> list[str]:
        return [e.value for e in cls]


@dataclass(frozen=True)
class CoursesEvent:
    event_name: CoursesEventType
    session_id: str
    timestamp: str
    page_path: str
