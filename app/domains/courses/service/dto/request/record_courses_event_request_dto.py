from dataclasses import dataclass

from app.domains.courses.domain.events.courses_event import CoursesEventType


@dataclass
class RecordCoursesEventRequestDto:
    event_name: CoursesEventType
    session_id: str
    timestamp: str
    page_path: str
