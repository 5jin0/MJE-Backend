import random
from typing import List, Optional, Set, Tuple

from app.domains.recommendation.domain.entity.course_candidate import CourseCandidate
from app.domains.recommendation.domain.value_object.activity_type import ActivityType
from app.domains.recommendation.domain.value_object.place import Place
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot

_DAYTIME_SLOTS = {TimeSlot.MORNING, TimeSlot.LUNCH, TimeSlot.AFTERNOON}

_DAYTIME_ACTIVITY_TYPES = {
    ActivityType.EXHIBITION.value,
    ActivityType.WALK.value,
    ActivityType.PARK.value,
    ActivityType.SHOPPING.value,
    ActivityType.EXPERIENCE.value,
    ActivityType.MOVIE.value,
}

_NIGHTTIME_ACTIVITY_TYPES = {ActivityType.NIGHTLIFE.value}

_WALK_TYPES = {ActivityType.WALK.value, ActivityType.PARK.value}

_COURSE_COUNT = 6
_POOL_PER_SLOT = 5


def _pick(pool: List[Place], rng: random.Random, exclude_keys: Optional[Set[str]] = None) -> Optional[Place]:
    candidates = [p for p in pool if (exclude_keys is None or p.place_key not in exclude_keys)]
    if not candidates:
        candidates = pool
    if not candidates:
        return None
    return rng.choice(candidates)


class CourseCandidateGeneratorService:
    def generate(
        self,
        restaurants: List[Place],
        cafes: List[Place],
        activities: List[Place],
        start_time: str,
        seed: Optional[int] = None,
    ) -> Tuple[List[CourseCandidate], List[str]]:
        rng = random.Random(seed)
        time_slot = TimeSlot.from_start_time(start_time)

        if time_slot in _DAYTIME_SLOTS:
            return self._generate_daytime(restaurants, cafes, activities, rng)
        return self._generate_evening(restaurants, cafes, activities, rng)

    def _generate_daytime(
        self,
        restaurants: List[Place],
        cafes: List[Place],
        activities: List[Place],
        rng: random.Random,
    ) -> Tuple[List[CourseCandidate], List[str]]:
        day_acts = [a for a in activities if a.activity_type in _DAYTIME_ACTIVITY_TYPES]
        reasons = self._shortage_reasons(restaurants, cafes, day_acts, "낮 활동")

        candidates: List[CourseCandidate] = []
        for _ in range(_COURSE_COUNT):
            r = _pick(restaurants, rng)
            c = _pick(cafes, rng)
            a = _pick(day_acts or activities, rng)
            if not (r and c and a):
                continue
            used = {r.place_key, c.place_key, a.place_key}
            if len(used) < 3:
                continue

            pattern = rng.choice([
                [a, r, c],
                [r, c, a],
                [r, a, c],
            ])
            candidates.append(CourseCandidate(places=pattern))

        candidates = self._deduplicate(candidates)
        return candidates, reasons

    def _generate_evening(
        self,
        restaurants: List[Place],
        cafes: List[Place],
        activities: List[Place],
        rng: random.Random,
    ) -> Tuple[List[CourseCandidate], List[str]]:
        night_acts = [a for a in activities if a.activity_type in _NIGHTTIME_ACTIVITY_TYPES]
        walk_acts = [a for a in activities if a.activity_type in _WALK_TYPES]
        reasons = self._shortage_reasons(restaurants, cafes, night_acts, "저녁 활동")

        candidates: List[CourseCandidate] = []
        for _ in range(_COURSE_COUNT):
            r = _pick(restaurants, rng)
            c = _pick(cafes, rng)
            na = _pick(night_acts, rng)
            wa = _pick(walk_acts or activities, rng)

            if not r:
                continue

            pattern_choices = []
            if c and na and r.place_key != c.place_key and r.place_key != na.place_key and c.place_key != na.place_key:
                pattern_choices.append([r, c, na])
            if na and wa and r.place_key != na.place_key and r.place_key != wa.place_key and na.place_key != wa.place_key:
                pattern_choices.append([r, na, wa])
            if c and wa and r.place_key != c.place_key and r.place_key != wa.place_key and c.place_key != wa.place_key:
                pattern_choices.append([r, c, wa])

            if not pattern_choices:
                continue
            candidates.append(CourseCandidate(places=rng.choice(pattern_choices)))

        candidates = self._deduplicate(candidates)
        return candidates, reasons

    def _deduplicate(self, candidates: List[CourseCandidate]) -> List[CourseCandidate]:
        seen: Set[Tuple[str, ...]] = set()
        unique: List[CourseCandidate] = []
        for c in candidates:
            key = tuple(p.place_key for p in c.places)
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _shortage_reasons(
        self,
        restaurants: List[Place],
        cafes: List[Place],
        activities: List[Place],
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
