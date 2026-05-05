from typing import List, Optional

from pydantic import BaseModel

from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    GetCourseDetailResponseDto,
)


class CourseDetailPlaceResponseForm(BaseModel):
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
    image_url: Optional[str]
    start_time: str
    end_time: str
    duration_minutes: int
    move_time_to_next_minutes: Optional[int]
    short_description: str


class OtherCourseResponseForm(BaseModel):
    course_id: str
    grade: str
    title: str
    route_summary: str
    area: str
    estimated_duration_minutes: int


class GetCourseDetailResponseForm(BaseModel):
    course_id: str
    grade: str
    area: str
    start_time: str
    transport: str
    title: str
    description: str
    estimated_duration_minutes: int
    places: List[CourseDetailPlaceResponseForm]
    other_courses: List[OtherCourseResponseForm]

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
            places=[
                CourseDetailPlaceResponseForm(
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
                    image_url=p.image_url,
                    start_time=p.start_time,
                    end_time=p.end_time,
                    duration_minutes=p.duration_minutes,
                    move_time_to_next_minutes=p.move_time_to_next_minutes,
                    short_description=p.short_description,
                )
                for p in dto.places
            ],
            other_courses=[
                OtherCourseResponseForm(
                    course_id=o.course_id,
                    grade=o.grade,
                    title=o.title,
                    route_summary=o.route_summary,
                    area=o.area,
                    estimated_duration_minutes=o.estimated_duration_minutes,
                )
                for o in dto.other_courses
            ],
        )
