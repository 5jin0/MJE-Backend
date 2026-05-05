from typing import List, Optional

from pydantic import BaseModel

from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    GetCourseDetailResponseDto,
)


class FrontendPlaceResponseForm(BaseModel):
    visitOrder: int
    name: str
    category: str
    durationMinutes: int
    photoUrl: Optional[str] = None
    description: Optional[str] = None
    routeDurationMin: Optional[int] = None


class FrontendSubCourseResponseForm(BaseModel):
    courseId: str
    courseType: str
    title: str
    routeSummary: str
    locationSummary: str
    totalDuration: int


class FrontendCourseDetailResponseForm(BaseModel):
    courseId: str
    title: str
    description: str
    totalDuration: int
    locationSummary: str
    routeSummary: str
    places: List[FrontendPlaceResponseForm]
    subCourses: List[FrontendSubCourseResponseForm]

    @classmethod
    def from_dto(cls, dto: GetCourseDetailResponseDto) -> "FrontendCourseDetailResponseForm":
        route_summary = " > ".join(p.name for p in dto.places)
        return cls(
            courseId=dto.course_id,
            title=dto.title,
            description=dto.description,
            totalDuration=dto.estimated_duration_minutes,
            locationSummary=dto.area,
            routeSummary=route_summary,
            places=[
                FrontendPlaceResponseForm(
                    visitOrder=p.order,
                    name=p.name,
                    category=p.category,
                    durationMinutes=p.duration_minutes,
                    photoUrl=p.image_url,
                    description=p.short_description,
                    routeDurationMin=p.move_time_to_next_minutes,
                )
                for p in dto.places
            ],
            subCourses=[
                FrontendSubCourseResponseForm(
                    courseId=o.course_id,
                    courseType=o.grade,
                    title=o.title,
                    routeSummary=o.route_summary,
                    locationSummary=o.area,
                    totalDuration=o.estimated_duration_minutes,
                )
                for o in dto.other_courses
            ],
        )


class FrontendOtherCourseItemForm(BaseModel):
    courseId: str
    name: str
    locations: List[str]
    duration: Optional[int] = None
    description: str


class FrontendOtherCoursesListForm(BaseModel):
    courses: List[FrontendOtherCourseItemForm]

    @classmethod
    def from_dto(cls, dto: GetCourseDetailResponseDto) -> "FrontendOtherCoursesListForm":
        return cls(
            courses=[
                FrontendOtherCourseItemForm(
                    courseId=o.course_id,
                    name=o.title,
                    locations=[o.area],
                    duration=o.estimated_duration_minutes,
                    description=o.route_summary,
                )
                for o in dto.other_courses
            ]
        )
