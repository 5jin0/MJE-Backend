from dataclasses import dataclass, field
from typing import List

from app.domains.courses.domain.value_object.recommendation_place import RecommendationPlace


@dataclass
class CoursePlace:
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
class CourseEntity:
    course_id: str
    grade: str
    area: str
    start_time: str
    transport: str
    title: str
    description: str
    estimated_duration_minutes: int
    restaurant: RecommendationPlace
    cafe: RecommendationPlace
    activity: RecommendationPlace
    places: List[CoursePlace] = field(default_factory=list)
