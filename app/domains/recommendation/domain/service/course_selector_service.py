from typing import List, Optional, Tuple

from app.domains.recommendation.domain.service.course_ordering_service import OrderedCourseResult
from app.domains.recommendation.domain.service.course_scorer_service import CourseScorerService
from app.domains.recommendation.domain.value_object.scored_course import ScoredCourse
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot
from app.domains.recommendation.domain.value_object.transport import Transport


class CourseSelectorService:
    def __init__(self) -> None:
        self._scorer = CourseScorerService()

    def select(
        self,
        ordered_results: List[OrderedCourseResult],
        time_slot: TimeSlot,
        transport: Transport,
    ) -> Tuple[Optional[ScoredCourse], List[ScoredCourse]]:
        if not ordered_results:
            return None, []

        scored = sorted(
            [self._scorer.score(r, time_slot, transport) for r in ordered_results],
            key=lambda c: c.total_score,
            reverse=True,
        )

        best = scored[0]
        best_ids = best.place_ids()

        # best 중복 페널티 적용 후 후보 정렬
        candidates = sorted(
            [self._scorer.score(c.ordered_result, time_slot, transport, best_ids) for c in scored[1:]],
            key=lambda c: c.total_score,
            reverse=True,
        )

        if not candidates:
            return best, []

        first_optional = candidates[0]

        # optional 2는 best + optional 1 모두와의 중복을 페널티
        avoid_ids = best_ids | first_optional.place_ids()
        second_candidates = sorted(
            [self._scorer.score(c.ordered_result, time_slot, transport, avoid_ids) for c in candidates[1:]],
            key=lambda c: c.total_score,
            reverse=True,
        )

        optionals = [first_optional]
        if second_candidates:
            optionals.append(second_candidates[0])

        return best, optionals
