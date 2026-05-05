from dataclasses import dataclass, field
from typing import List


@dataclass
class CoursePlaceDto:
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
    places: List[CoursePlaceDto] = field(default_factory=list)
