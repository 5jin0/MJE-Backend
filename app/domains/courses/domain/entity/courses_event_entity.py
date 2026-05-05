from dataclasses import dataclass
from typing import Optional

from app.domains.courses.domain.events.courses_event import CoursesEventType


@dataclass
class CoursesEventEntity:
    event_name: CoursesEventType
    session_id: str
    timestamp: str
    page_path: str
    id: Optional[int] = None
