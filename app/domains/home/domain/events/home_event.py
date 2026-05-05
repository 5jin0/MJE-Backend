from dataclasses import dataclass
from enum import Enum


class HomeEventType(Enum):
    VIEW_HOME = "view_home"
    LOGO_CLICK = "logo_click"
    HOME_CLICK = "home_click"

    @classmethod
    def allowed_values(cls) -> list[str]:
        return [e.value for e in cls]


@dataclass(frozen=True)
class HomeEvent:
    event_name: HomeEventType
    session_id: str
    timestamp: str
    page_path: str
