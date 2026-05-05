from app.domains.courses.domain.entity.courses_event_entity import CoursesEventEntity
from app.domains.courses.repository.courses_event_repository_interface import CoursesEventRepositoryInterface
from app.domains.courses.service.dto.request.record_courses_event_request_dto import RecordCoursesEventRequestDto
from app.domains.courses.service.dto.response.record_courses_event_response_dto import RecordCoursesEventResponseDto


class RecordCoursesEventUseCase:
    def __init__(self, repository: CoursesEventRepositoryInterface) -> None:
        self._repository = repository

    async def execute(self, dto: RecordCoursesEventRequestDto) -> RecordCoursesEventResponseDto:
        entity = CoursesEventEntity(
            event_name=dto.event_name,
            session_id=dto.session_id,
            timestamp=dto.timestamp,
            page_path=dto.page_path,
        )
        await self._repository.save(entity)
        return RecordCoursesEventResponseDto(success=True)
