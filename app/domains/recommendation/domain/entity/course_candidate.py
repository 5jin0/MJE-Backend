from dataclasses import dataclass
from typing import List

from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace


@dataclass
class CourseCandidate:
    places: List[CandidatePlace]  # 방문 순서대로 정렬된 장소 목록 (3개)
