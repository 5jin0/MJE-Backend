from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from app.domains.courses.domain.events.courses_event import CoursesEventType
from app.domains.courses.service.dto.request.record_courses_event_request_dto import RecordCoursesEventRequestDto


class CourseEventRequestForm(BaseModel):
    event_name: str
    session_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    page_path: str = ""

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        allowed = CoursesEventType.allowed_values()
        if v not in allowed:
            raise ValueError(f"event_name must be one of {allowed}")
        return v

    def to_request(self) -> RecordCoursesEventRequestDto:
        return RecordCoursesEventRequestDto(
            event_name=CoursesEventType(self.event_name),
            session_id=self.session_id,
            timestamp=self.timestamp,
            page_path=self.page_path,
        )
