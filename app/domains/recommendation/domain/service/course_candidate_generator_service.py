from itertools import product
from typing import List, Set, Tuple

from app.domains.recommendation.domain.entity.course_candidate import CourseCandidate
from app.domains.recommendation.domain.value_object.activity_type import ActivityKind
from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot

MIN_CANDIDATES = 5

_DAYTIME_SLOTS: Set[TimeSlot] = {TimeSlot.LUNCH, TimeSlot.AFTERNOON}

# 낮 전용 활동: 보드게임, 전시, 공방, 영화관, 만화/북카페 + 쇼핑/팝업/스포츠
_DAYTIME_KINDS: Set[ActivityKind] = {
    ActivityKind.INDOOR_PLAY,
    ActivityKind.EXHIBITION,
    ActivityKind.WORKSHOP,
    ActivityKind.MOVIE,
    ActivityKind.SHOPPING,
    ActivityKind.POPUP,
    ActivityKind.SPORTS,
    ActivityKind.BOOK_CAFE,
}

# 저녁 전용 활동: 술집, 바, 심야데이트 + 노래방/야경
_EVENING_KINDS: Set[ActivityKind] = {
    ActivityKind.BAR,
    ActivityKind.LATE_NIGHT,
    ActivityKind.KARAOKE,
    ActivityKind.NIGHT_VIEW,
}


class CourseCandidateGeneratorService:
    def generate(
        self,
        restaurant_candidates: List[CandidatePlace],
        cafe_candidates: List[CandidatePlace],
        activity_candidates: List[CandidatePlace],
        start_time: str,
    ) -> Tuple[List[CourseCandidate], List[str]]:
        time_slot = TimeSlot.from_start_time(start_time)
        if time_slot in _DAYTIME_SLOTS:
            return self._generate_daytime(restaurant_candidates, cafe_candidates, activity_candidates)
        return self._generate_evening(restaurant_candidates, cafe_candidates, activity_candidates)

    def _generate_daytime(
        self,
        restaurants: List[CandidatePlace],
        cafes: List[CandidatePlace],
        activities: List[CandidatePlace],
    ) -> Tuple[List[CourseCandidate], List[str]]:
        acts = [a for a in activities if a.activity_kind in _DAYTIME_KINDS]
        candidates: List[CourseCandidate] = []

        for r, c, a in product(restaurants, cafes, acts):
            # 3가지 방문 순서: 활동-식당-카페 / 식당-카페-활동 / 식당-활동-카페
            for ordered in ([a, r, c], [r, c, a], [r, a, c]):
                if not self._has_duplicate(*ordered):
                    candidates.append(CourseCandidate(places=list(ordered)))

        reasons = self._check_shortages(restaurants, cafes, acts, "활동")
        if len(candidates) < MIN_CANDIDATES:
            reasons.append(f"코스 후보가 {MIN_CANDIDATES}개 미만입니다 (현재 {len(candidates)}개)")
        return candidates, reasons

    def _generate_evening(
        self,
        restaurants: List[CandidatePlace],
        cafes: List[CandidatePlace],
        activities: List[CandidatePlace],
    ) -> Tuple[List[CourseCandidate], List[str]]:
        evening_acts = [a for a in activities if a.activity_kind in _EVENING_KINDS]
        walks = [a for a in activities if a.activity_kind == ActivityKind.WALK]
        candidates: List[CourseCandidate] = []

        # 식당-카페-활동 (술집/노래방/야경/심야)
        for r, c, a in product(restaurants, cafes, evening_acts):
            if not self._has_duplicate(r, c, a):
                candidates.append(CourseCandidate(places=[r, c, a]))

        # 식당-술집-산책
        for r, a, w in product(restaurants, evening_acts, walks):
            if not self._has_duplicate(r, a, w):
                candidates.append(CourseCandidate(places=[r, a, w]))

        # 식당-카페-산책
        for r, c, w in product(restaurants, cafes, walks):
            if not self._has_duplicate(r, c, w):
                candidates.append(CourseCandidate(places=[r, c, w]))

        reasons = self._check_shortages(restaurants, cafes, evening_acts, "저녁 활동")
        if len(candidates) < MIN_CANDIDATES:
            reasons.append(f"코스 후보가 {MIN_CANDIDATES}개 미만입니다 (현재 {len(candidates)}개)")
        return candidates, reasons

    def _has_duplicate(self, *places: CandidatePlace) -> bool:
        ids = [p.id for p in places]
        if len(ids) != len(set(ids)):
            return True
        name_addresses = [(p.name, p.address) for p in places]
        return len(name_addresses) != len(set(name_addresses))

    def _check_shortages(
        self,
        restaurants: List[CandidatePlace],
        cafes: List[CandidatePlace],
        activities: List[CandidatePlace],
        activity_label: str,
    ) -> List[str]:
        reasons = []
        if not restaurants:
            reasons.append("레스토랑 후보가 없습니다")
        if not cafes:
            reasons.append("카페 후보가 없습니다")
        if not activities:
            reasons.append(f"{activity_label} 후보가 없습니다")
        return reasons
