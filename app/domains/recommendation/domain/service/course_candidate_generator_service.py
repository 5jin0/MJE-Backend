from itertools import product
from typing import List, Tuple

from app.domains.recommendation.domain.entity.course_candidate import CourseCandidate
from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace

MIN_CANDIDATES = 10


class CourseCandidateGeneratorService:
    def generate(
        self,
        restaurant_candidates: List[CandidatePlace],
        cafe_candidates: List[CandidatePlace],
        activity_candidates: List[CandidatePlace],
    ) -> Tuple[List[CourseCandidate], List[str]]:
        shortage_reasons = self._check_input_shortages(
            restaurant_candidates, cafe_candidates, activity_candidates
        )

        candidates = [
            CourseCandidate(restaurant=r, cafe=c, activity=a)
            for r, c, a in product(restaurant_candidates, cafe_candidates, activity_candidates)
            if not self._has_duplicate(r, c, a)
        ]

        if len(candidates) < MIN_CANDIDATES:
            shortage_reasons.append(
                f"코스 후보가 {MIN_CANDIDATES}개 미만입니다 (현재 {len(candidates)}개)"
            )

        return candidates, shortage_reasons

    def _has_duplicate(self, r: CandidatePlace, c: CandidatePlace, a: CandidatePlace) -> bool:
        places = [r, c, a]
        ids = [p.id for p in places]
        if len(ids) != len(set(ids)):
            return True
        name_addresses = [(p.name, p.address) for p in places]
        if len(name_addresses) != len(set(name_addresses)):
            return True
        return False

    def _check_input_shortages(
        self,
        restaurants: List[CandidatePlace],
        cafes: List[CandidatePlace],
        activities: List[CandidatePlace],
    ) -> List[str]:
        reasons = []
        if not restaurants:
            reasons.append("레스토랑 후보가 없습니다")
        if not cafes:
            reasons.append("카페 후보가 없습니다")
        if not activities:
            reasons.append("액티비티 후보가 없습니다")
        return reasons
