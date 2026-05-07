from typing import List, Optional, Tuple

from app.domains.recommendation.domain.entity.course_candidate import Course, CourseCandidate
from app.domains.recommendation.domain.service.course_scorer_service import CourseScorerService
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot
from app.domains.recommendation.domain.value_object.transport import Transport


class CourseSelectorService:
    def __init__(self) -> None:
        self._scorer = CourseScorerService()

    def select(
        self,
        candidates: List[CourseCandidate],
        start_time: str,
        transport: Transport,
        time_slot: TimeSlot,
    ) -> Tuple[Optional[Course], List[Course]]:
        if not candidates:
            return None, []

        scored = sorted(
            [
                self._scorer.score_and_build(c, start_time, transport, time_slot)
                for c in candidates
            ],
            key=lambda c: c.total_score,
            reverse=True,
        )

        valid = [c for c in scored if c.is_valid]
        if not valid:
            valid = scored

        best = valid[0]
        best_keys = best.place_keys()

        optionals: List[Course] = []
        for course in valid[1:]:
            overlap = len(course.place_keys() & best_keys)
            penalty = overlap * 0.15
            course.total_score = max(0.0, course.total_score - penalty)
            optionals.append(course)

        optionals.sort(key=lambda c: c.total_score, reverse=True)

        if len(optionals) >= 2:
            second_keys = optionals[0].place_keys() | best_keys
            for course in optionals[1:]:
                overlap = len(course.place_keys() & second_keys)
                course.total_score = max(0.0, course.total_score - overlap * 0.15)
            optionals[1:] = sorted(optionals[1:], key=lambda c: c.total_score, reverse=True)

        return best, optionals[:2]
