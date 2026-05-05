from dataclasses import dataclass

from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace


@dataclass
class CourseCandidate:
    restaurant: CandidatePlace
    cafe: CandidatePlace
    activity: CandidatePlace
