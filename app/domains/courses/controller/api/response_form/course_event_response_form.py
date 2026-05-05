from pydantic import BaseModel

from app.domains.courses.service.dto.response.record_courses_event_response_dto import RecordCoursesEventResponseDto


class CourseEventResponseForm(BaseModel):
    success: bool

    @classmethod
    def from_response(cls, dto: RecordCoursesEventResponseDto) -> "CourseEventResponseForm":
        return cls(success=dto.success)
