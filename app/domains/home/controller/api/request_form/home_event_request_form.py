from pydantic import BaseModel, field_validator

from app.domains.home.domain.events.home_event import HomeEventType
from app.domains.home.service.dto.request.record_home_event_request_dto import RecordHomeEventRequestDto


class HomeEventRequestForm(BaseModel):
    event_name: str
    session_id: str
    timestamp: str
    page_path: str

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        allowed = HomeEventType.allowed_values()
        if v not in allowed:
            raise ValueError(f"event_name must be one of {allowed}")
        return v

    def to_request(self) -> RecordHomeEventRequestDto:
        return RecordHomeEventRequestDto(
            event_name=HomeEventType(self.event_name),
            session_id=self.session_id,
            timestamp=self.timestamp,
            page_path=self.page_path,
        )
