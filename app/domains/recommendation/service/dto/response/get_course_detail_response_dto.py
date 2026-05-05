from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CourseDetailPlaceDto:
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


@dataclass
class OtherCourseDto:
    course_id: str
    grade: str
    title: str
    route_summary: str
    area: str
    estimated_duration_minutes: int


@dataclass
class GetCourseDetailResponseDto:
    course_id: str
    grade: str
    area: str
    start_time: str
    transport: str
    title: str
    description: str
    estimated_duration_minutes: int
    places: List[CourseDetailPlaceDto] = field(default_factory=list)
    other_courses: List[OtherCourseDto] = field(default_factory=list)
