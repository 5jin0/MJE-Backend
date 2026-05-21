from typing import List, Optional

from pydantic import BaseModel

from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    GetCourseDetailResponseDto,
)


def _build_grade_map(courses: list) -> dict:
    optional_index = 0
    grade_map = {}
    for o in courses:
        if o.grade == "best":
            grade_map[o.course_id] = "best"
        else:
            grade_map[o.course_id] = "optional_a" if optional_index == 0 else "optional_b"
            optional_index += 1
    return grade_map


class FrontendPlaceResponseForm(BaseModel):
    visitOrder: int
    name: str
    category: str
    durationMinutes: int
    photoUrl: Optional[str] = None
    description: Optional[str] = None
    routeDurationMin: Optional[int] = None
    address: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None


class FrontendSubCourseResponseForm(BaseModel):
    courseId: str
    courseType: str
    title: str
    routeSummary: str
    locationSummary: str
    totalDuration: int


class FrontendCourseDetailResponseForm(BaseModel):
    courseId: str
    courseType: str
    title: str
    description: str
    totalDuration: int
    locationSummary: str
    routeSummary: str
    transport: str
    places: List[FrontendPlaceResponseForm]
    subCourses: List[FrontendSubCourseResponseForm]

    @classmethod
    def from_dto(cls, dto: GetCourseDetailResponseDto) -> "FrontendCourseDetailResponseForm":
        grade_map = _build_grade_map(dto.other_courses)
        route_summary = " > ".join(p.name for p in dto.places)
        return cls(
            courseId=dto.course_id,
            courseType=grade_map.get(dto.course_id, dto.grade),
            title=dto.title,
            description=dto.description,
            totalDuration=dto.estimated_duration_minutes,
            locationSummary=dto.area,
            routeSummary=route_summary,
            transport=dto.transport,
            places=[
                FrontendPlaceResponseForm(
                    visitOrder=p.order,
                    name=p.name,
                    category=p.category,
                    durationMinutes=p.duration_minutes,
                    photoUrl=p.image_url,
                    description=p.short_description,
                    routeDurationMin=p.move_time_to_next_minutes,
                    address=p.road_address or p.address,
                    startTime=p.start_time,
                    endTime=p.end_time,
                )
                for p in dto.places
            ],
            subCourses=[
                FrontendSubCourseResponseForm(
                    courseId=o.course_id,
                    courseType=grade_map.get(o.course_id, o.grade),
                    title=o.title,
                    routeSummary=o.route_summary,
                    locationSummary=o.area,
                    totalDuration=o.estimated_duration_minutes,
                )
                for o in dto.other_courses
                if o.course_id != dto.course_id
            ],
        )


class FrontendPlaceDetailItemForm(BaseModel):
    id: str
    time: Optional[str] = None
    location: str
    name: str
    description: str
    imageUrl: Optional[str] = None


class FrontendActivitiesListForm(BaseModel):
    activities: List[FrontendPlaceDetailItemForm]

    @classmethod
    def from_dto(cls, dto: GetCourseDetailResponseDto) -> "FrontendActivitiesListForm":
        return cls(
            activities=[
                FrontendPlaceDetailItemForm(
                    id=f"{dto.course_id}-{p.order}",
                    time=p.start_time or None,
                    location=p.road_address or p.address,
                    name=p.name,
                    description=p.short_description,
                    imageUrl=p.image_url,
                )
                for p in dto.places
                if p.place_type == "activity"
            ]
        )


class FrontendCafesListForm(BaseModel):
    cafes: List[FrontendPlaceDetailItemForm]

    @classmethod
    def from_dto(cls, dto: GetCourseDetailResponseDto) -> "FrontendCafesListForm":
        return cls(
            cafes=[
                FrontendPlaceDetailItemForm(
                    id=f"{dto.course_id}-{p.order}",
                    time=p.start_time or None,
                    location=p.road_address or p.address,
                    name=p.name,
                    description=p.short_description,
                    imageUrl=p.image_url,
                )
                for p in dto.places
                if p.place_type == "cafe"
            ]
        )


class FrontendRestaurantsListForm(BaseModel):
    restaurants: List[FrontendPlaceDetailItemForm]

    @classmethod
    def from_dto(cls, dto: GetCourseDetailResponseDto) -> "FrontendRestaurantsListForm":
        return cls(
            restaurants=[
                FrontendPlaceDetailItemForm(
                    id=f"{dto.course_id}-{p.order}",
                    time=p.start_time or None,
                    location=p.road_address or p.address,
                    name=p.name,
                    description=p.short_description,
                    imageUrl=p.image_url,
                )
                for p in dto.places
                if p.place_type == "restaurant"
            ]
        )


class FrontendOtherCourseItemForm(BaseModel):
    courseId: str
    courseType: str
    name: str
    places: List[str]
    locations: List[str]
    duration: Optional[int] = None
    description: str


class FrontendOtherCoursesListForm(BaseModel):
    courses: List[FrontendOtherCourseItemForm]

    @classmethod
    def from_dto(cls, dto: GetCourseDetailResponseDto) -> "FrontendOtherCoursesListForm":
        grade_map = _build_grade_map(dto.other_courses)
        courses = [
            FrontendOtherCourseItemForm(
                courseId=o.course_id,
                courseType=grade_map.get(o.course_id, o.grade),
                name=o.title,
                places=o.places,
                locations=[o.area],
                duration=o.estimated_duration_minutes,
                description=o.route_summary,
            )
            for o in dto.other_courses
            if o.course_id != dto.course_id
        ]
        return cls(courses=courses)
