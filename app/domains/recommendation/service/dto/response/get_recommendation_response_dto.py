from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RecommendationPlaceDto:
    order: int
    place_type: str
    name: str
    category: str
    road_address: str
    address: str
    latitude: float
    longitude: float
    link: str
    telephone: str
    activity_type: Optional[str]
    duration_minutes: int
    start_time: str
    end_time: str
    image_url: Optional[str] = None


@dataclass
class RecommendationCourseItemDto:
    course_id: str
    grade: str
    places: List[RecommendationPlaceDto]
    image_url: Optional[str] = None


@dataclass
class GetRecommendationResponseDto:
    courses: List[RecommendationCourseItemDto]
    shortage_reasons: List[str] = field(default_factory=list)
