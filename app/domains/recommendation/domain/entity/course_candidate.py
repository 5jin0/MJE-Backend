from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from app.domains.recommendation.domain.value_object.place import Place


@dataclass
class CoursePlace:
    place: Place
    order: int
    duration_minutes: int
    move_minutes_to_next: int
    start_time: str
    end_time: str


@dataclass
class CourseCandidate:
    places: List[Place]


@dataclass
class Course:
    places: List[CoursePlace]
    total_score: float
    is_valid: bool
    course_id: str = ""
    grade: str = "best"

    def place_keys(self) -> Set[str]:
        return {cp.place.place_key for cp in self.places}
