from pydantic import BaseModel

from app.domains.home.service.dto.response.record_home_event_response_dto import RecordHomeEventResponseDto


class HomeEventResponseForm(BaseModel):
    success: bool

    @classmethod
    def from_response(cls, dto: RecordHomeEventResponseDto) -> "HomeEventResponseForm":
        return cls(success=dto.success)
