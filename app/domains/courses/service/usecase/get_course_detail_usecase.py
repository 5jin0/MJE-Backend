from app.common.exceptions import NotFoundError
from app.domains.courses.repository.course_repository_interface import CourseRepositoryInterface
from app.domains.courses.service.dto.response.get_course_detail_response_dto import (
    CoursePlaceDto,
    GetCourseDetailResponseDto,
)


class GetCourseDetailUseCase:
    def __init__(self, repository: CourseRepositoryInterface) -> None:
        self._repository = repository

    def execute(self, course_id: str) -> GetCourseDetailResponseDto:
        entity = self._repository.find_by_id(course_id)
        if entity is None:
            raise NotFoundError(f"코스를 찾을 수 없습니다: {course_id}")

        places = [
            CoursePlaceDto(
                order=p.order,
                place_type=p.place_type,
                id=p.id,
                name=p.name,
                category=p.category,
                road_address=p.road_address,
                address=p.address,
                mapx=p.mapx,
                mapy=p.mapy,
                link=p.link,
                telephone=p.telephone,
                keyword=p.keyword,
                collected_at=p.collected_at,
                start_time=p.start_time,
                end_time=p.end_time,
                duration_minutes=p.duration_minutes,
                move_time_to_next_minutes=p.move_time_to_next_minutes,
            )
            for p in entity.places
        ]

        return GetCourseDetailResponseDto(
            course_id=entity.course_id,
            grade=entity.grade,
            area=entity.area,
            start_time=entity.start_time,
            transport=entity.transport,
            title=entity.title,
            description=entity.description,
            estimated_duration_minutes=entity.estimated_duration_minutes,
            places=places,
        )
