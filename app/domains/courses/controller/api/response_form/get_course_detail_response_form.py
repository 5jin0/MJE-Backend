from typing import List

from pydantic import BaseModel

from app.domains.courses.service.dto.response.get_course_detail_response_dto import (
    GetCourseDetailResponseDto,
)


class CoursePlaceResponseForm(BaseModel):
    order: int
    place_type: str
    id: int
    name: str
    category: str
    road_address: str
    address: str
    mapx: str
    mapy: str
    link: str
    telephone: str
    keyword: str
    collected_at: str
    start_time: str
    end_time: str
    duration_minutes: int
    move_time_to_next_minutes: int


class GetCourseDetailResponseForm(BaseModel):
    course_id: str
    grade: str
    area: str
    start_time: str
    transport: str
    title: str
    description: str
    estimated_duration_minutes: int
    places: List[CoursePlaceResponseForm]

    @classmethod
    def from_response(cls, dto: GetCourseDetailResponseDto) -> "GetCourseDetailResponseForm":
        return cls(
            course_id=dto.course_id,
            grade=dto.grade,
            area=dto.area,
            start_time=dto.start_time,
            transport=dto.transport,
            title=dto.title,
            description=dto.description,
            estimated_duration_minutes=dto.estimated_duration_minutes,
            places=[CoursePlaceResponseForm(**vars(p)) for p in dto.places],
        )
