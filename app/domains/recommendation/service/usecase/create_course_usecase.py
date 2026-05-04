from __future__ import annotations

import html
import logging
import re
import uuid
from datetime import time

from app.domains.recommendation.domain.entity.course import Course
from app.domains.recommendation.domain.entity.place import Place
from app.domains.recommendation.domain.service.course_composer import CourseComposer
from app.domains.recommendation.domain.service.recommendation_config import (
    ACTIVITY_SUBTYPE_FALLBACK_SEARCH_KEYWORDS,
    ACTIVITY_SUBTYPE_SEARCH_KEYWORDS,
    ACTIVITY_SUBTYPE_SIGNALS,
    CATEGORY_SEARCH_KEYWORDS,
    MIN_ACTIVITY_CANDIDATES,
    TOP_N_CANDIDATES,
)
from app.domains.recommendation.domain.service.rule_scorer import RuleScorer
from app.domains.recommendation.domain.service.time_slot_filter import TimeSlotFilter
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot
from app.domains.recommendation.domain.value_object.transport import Transport
from app.domains.recommendation.service.dto.request.create_course_request_dto import CreateCourseRequestDto
from app.domains.recommendation.service.dto.response.create_course_response_dto import (
    CourseTitlePlaceDto,
    CourseResultDto,
    CreateCourseResponseDto,
    PlaceResultDto,
)
from app.domains.recommendation.service.port.course_store_port import CourseStorePort
from app.domains.recommendation.service.port.naver_datalab_port import NaverDatalabPort
from app.domains.recommendation.service.port.naver_map_port import NaverMapPort
from app.domains.recommendation.service.port.naver_search_port import NaverSearchPort

_INSUFFICIENT_MESSAGE = (
    "해당 조건에 맞는 추천 후보가 부족합니다. "
    "지역 또는 이동수단을 변경해 다시 시도해주세요."
)

_BRAND_CAP = 2
_KEYWORD_TYPE_CAP = 3

_IMAGE_EXCLUDE_KEYWORDS = frozenset({"협찬", "광고", "제공받아", "부동산", "분양"})
_IMAGE_HARD_EXCLUDE_KEYWORDS = frozenset(
    {"map", "logo", "banner", "poster", "ad", "guide", "capture"}
)
_IMAGE_STOCK_EXCLUDE_KEYWORDS = frozenset(
    {"unsplash", "pexels", "pixabay", "shutterstock", "stock"}
)
_IMAGE_SOURCE_EXCLUDE_KEYWORDS = frozenset(
    {"pinterest", "pinimg", "instagram", "cdninstagram", "kmong", "blog", "postfiles", "menupan"}
)
_IMAGE_MENU_EXCLUDE_KEYWORDS = frozenset(
    {"menu", "drink", "beverage", "goods", "product", "delivery", "package", "gift", "메뉴", "음료", "상품", "배달", "포장", "선물"}
)
_IMAGE_PREFERRED_SOURCE_KEYWORDS = frozenset(
    {"ldb-phinf", "phinf", "naver"}
)
_IMAGE_PEOPLE_EXCLUDE_KEYWORDS = frozenset(
    {"face", "selfie", "profile", "portrait", "woman", "man", "person", "people", "모델", "인물", "여자", "남자"}
)
_IMAGE_SCENIC_EXCLUDE_KEYWORDS = frozenset(
    {"lake", "forest", "mountain", "river", "canoe", "camping", "nature", "landscape", "호수", "숲", "산", "강", "캠핑"}
)
_IMAGE_LOOKUP_LIMIT_PER_REQUEST = 4
_BOLD_RE = re.compile(r"</?b>")
_GENERIC_TITLE_PHRASES = frozenset({
    "맛집",
    "카페",
    "디저트 카페",
    "브런치 카페",
    "브런치",
    "전시",
    "체험",
    "산책",
    "영화",
    "쇼핑",
    "야경",
    "액티비티",
    "데이트",
})

ALL_CATEGORIES = ["restaurant", "cafe", "activity"]

_CATEGORY_SIGNALS: dict[str, tuple[str, ...]] = {
    "restaurant": ("음식", "식당", "맛집", "요리", "주점", "술집", "포차", "바", "레스토랑"),
    "cafe": ("카페", "커피", "디저트", "베이커리", "브런치", "와인바", "칵테일바"),
    "activity": ("전시", "체험", "공방", "영화", "볼링", "방탈출", "갤러리", "공원", "산책", "클라이밍", "편집숍", "홀덤"),
}

CATEGORY_IMAGE_SUFFIX = {
    "restaurant": "음식 사진",
    "cafe": "카페 외관",
    "activity": "체험",
}
ACTIVITY_SUBTYPE_IMAGE_SUFFIX = {
    "culture": "전시 공간",
    "experience": "체험 공간",
    "walk": "산책 야경",
    "nightlife": "바 내부",
    "shopping": "쇼룸 매장",
}

# Datalab 쿼리용: {area} + 아래 키워드 조합으로 카테고리별 인기도 수집
CATEGORY_TREND_KEYWORD = {
    "restaurant": "맛집",
    "cafe": "카페",
    "activity": "이색체험",
}

_MAJOR_FRANCHISE: frozenset[str] = frozenset({
    "스타벅스", "투썸플레이스", "이디야", "메가커피", "컴포즈커피", "빽다방",
    "폴바셋", "탐앤탐스", "할리스", "커피빈", "파스쿠찌", "카페베네",
    "더벤티", "엔젤리너스", "공차", "던킨",
})


logger = logging.getLogger(__name__)


class CreateCourseUseCase:

    def __init__(
        self,
        naver_search: NaverSearchPort,
        naver_datalab: NaverDatalabPort,
        naver_map: NaverMapPort,
        course_store: CourseStorePort,
    ) -> None:
        self._search = naver_search
        self._datalab = naver_datalab
        self._map = naver_map
        self._course_store = course_store
        self._slot_filter = TimeSlotFilter()
        self._scorer = RuleScorer()
        self._composer = CourseComposer()
        self._place_search_cache: dict[tuple[str, str, int], list[dict]] = {}
        self._image_lookup_count = 0
        self._image_lookup_rate_limited = False
        self._image_cache: dict[tuple[str, str, str], str | None] = {}

    async def execute(self, dto: CreateCourseRequestDto) -> CreateCourseResponseDto:
        self._image_lookup_count = 0
        self._image_lookup_rate_limited = False
        self._image_cache.clear()

        start_time = self._parse_time(dto.start_time)
        time_slot = TimeSlot.from_time(start_time)
        transport = Transport.from_str(dto.transport)

        # 1. 카테고리별 트렌드 수집 — 장소 후보 수집량 결정 기준
        category_trends = await self._collect_category_trends(dto.area)

        # 2. 트렌드 기반 장소 후보 수집 (트렌딩 카테고리 → 더 많은 후보)
        places_by_category = await self._collect_places(dto.area, category_trends, time_slot)

        # 3. 시간대 필터링 (Domain Service)
        filtered = {
            cat: self._slot_filter.filter(places, time_slot)
            for cat, places in places_by_category.items()
        }

        # 4. 차량 이동 시 주차 정보 조회
        if transport.requires_parking_check():
            for places in filtered.values():
                for place in places:
                    place.has_parking = await self._search.search_parking(place.road_address)

        # 5. 장소 점수 계산
        self._scorer.apply_scores(filtered, category_trends, time_slot, transport)

        # 6. 코스 조합 — 가중 랜덤 선택
        courses = self._composer.compose(filtered, time_slot, transport)
        self._log_recommendation_diagnostics(
            dto=dto,
            time_slot=time_slot,
            transport=transport,
            places_by_category=places_by_category,
            filtered_places=filtered,
            courses=courses,
        )

        main, sub1, sub2 = self._scorer.rank_courses(courses)

        # 7. 최종 코스 장소에만 이미지 보강
        final_courses = [c for c in [main, sub1, sub2] if c is not None]
        await self._enrich_final_course_images(final_courses)

        # 8. 최종 코스에 한해 Naver 지도 API로 실제 이동소요시간·동선 보강
        await self._enrich_with_routes(final_courses, dto.transport)

        recommendation_id = str(uuid.uuid4())
        response = self._build_response(
            main,
            sub1,
            sub2,
            dto.area,
            time_slot,
            len(courses),
            recommendation_id,
        )
        self._course_store.save(recommendation_id, response)
        return response

    async def _enrich_final_course_images(self, courses: list[Course]) -> None:
        seen_places: set[tuple[str, str, str]] = set()
        for course in courses:
            for course_place in course.places:
                place = course_place.place
                key = (place.name, place.area, place.category)
                if key in seen_places:
                    continue
                seen_places.add(key)
                place.image_url = await self._fetch_image(place, place.category)

    # ── 트렌드 수집 ───────────────────────────────────────────────────────────

    async def _collect_category_trends(self, area: str) -> dict[str, float]:
        """Datalab으로 지역별 카테고리 트렌드 사전 수집 — 장소 후보 수집량 결정에 사용"""
        keywords = [f"{area} {CATEGORY_TREND_KEYWORD[cat]}" for cat in ALL_CATEGORIES]
        try:
            scores = await self._datalab.get_trend_scores(keywords[:5])
            return {
                cat: scores.get(f"{area} {CATEGORY_TREND_KEYWORD[cat]}", 0.0)
                for cat in ALL_CATEGORIES
            }
        except Exception:
            return {cat: 0.0 for cat in ALL_CATEGORIES}

    # ── 장소 수집 ─────────────────────────────────────────────────────────────

    async def _collect_places(
        self, area: str, category_trends: dict[str, float], time_slot: TimeSlot
    ) -> dict[str, list[Place]]:
        """트렌드 점수가 높은 카테고리일수록 더 많은 후보 수집 (10~40개)"""
        result: dict[str, list[Place]] = {}
        for cat in ALL_CATEGORIES:
            trend_score = category_trends.get(cat, 0.0)
            display = max(10, min(40, int(20 + trend_score * 20)))
            if cat == "activity":
                result[cat] = await self._collect_activity_places(
                    area=area,
                    time_slot=time_slot,
                    display=display,
                )
                continue
            raw: list[dict] = []
            target_count = TOP_N_CANDIDATES if cat != "activity" else max(
                TOP_N_CANDIDATES,
                MIN_ACTIVITY_CANDIDATES,
            )
            for kw in CATEGORY_SEARCH_KEYWORDS[cat][time_slot.value]:
                query = f"{area} {kw}"
                items = await self._search_places_cached(query, cat, display)
                raw.extend(items)
                interim_places = [self._to_place(item, cat, rank) for rank, item in enumerate(raw, 1)]
                interim_sanitized = self._sanitize_places(area, cat, interim_places)
                self._log_collection_query(
                    area=area,
                    category=cat,
                    query=query,
                    fetched_count=len(items),
                    accumulated_count=len(raw),
                    sanitized_count=len(interim_sanitized),
                    target_count=target_count,
                )
                if len(interim_sanitized) >= target_count:
                    break
            candidates = [self._to_place(item, cat, rank) for rank, item in enumerate(raw, 1)]
            sanitized = self._sanitize_places(area, cat, candidates)

            if cat == "activity" and len(sanitized) < MIN_ACTIVITY_CANDIDATES:
                fallback_raw = await self._collect_activity_fallback_places(
                    area=area,
                    time_slot=time_slot,
                    display=max(8, display // 2),
                )
                fallback_candidates = [
                    self._to_place(item, cat, rank)
                    for rank, item in enumerate(fallback_raw, len(candidates) + 1)
                ]
                sanitized = self._sanitize_places(area, cat, candidates + fallback_candidates)
                logger.info(
                    "recommendation.activity_fallback area=%s time_slot=%s fetched=%s sanitized=%s target=%s",
                    area,
                    time_slot.value,
                    len(fallback_raw),
                    len(sanitized),
                    MIN_ACTIVITY_CANDIDATES,
                )

            diversified = self._diversify_places(sanitized)
            result[cat] = diversified
            logger.info(
                "recommendation.category_pool area=%s category=%s time_slot=%s raw=%s sanitized=%s diversified=%s samples=%s",
                area,
                cat,
                time_slot.value,
                len(raw),
                len(sanitized),
                len(diversified),
                self._sample_place_names(diversified),
            )
        return result

    async def _collect_activity_places(
        self,
        area: str,
        time_slot: TimeSlot,
        display: int,
    ) -> list[Place]:
        raw: list[tuple[dict, str]] = []
        target_count = max(TOP_N_CANDIDATES, MIN_ACTIVITY_CANDIDATES)
        subtype_keywords = ACTIVITY_SUBTYPE_SEARCH_KEYWORDS.get(time_slot.value, {})

        for subtype, keywords in subtype_keywords.items():
            for kw in keywords:
                query = f"{area} {kw}"
                items = await self._search_places_cached(query, "activity", display)
                raw.extend((item, subtype) for item in items)
                interim_places = [
                    self._to_place(item, "activity", rank, subtype_hint=subtype_hint)
                    for rank, (item, subtype_hint) in enumerate(raw, 1)
                ]
                interim_sanitized = self._sanitize_places(area, "activity", interim_places)
                self._log_collection_query(
                    area=area,
                    category="activity",
                    query=query,
                    fetched_count=len(items),
                    accumulated_count=len(raw),
                    sanitized_count=len(interim_sanitized),
                    target_count=target_count,
                    subtype=subtype,
                )
                if len(interim_sanitized) >= target_count:
                    break
            if len(raw) >= target_count:
                break

        candidates = [
            self._to_place(item, "activity", rank, subtype_hint=subtype)
            for rank, (item, subtype) in enumerate(raw, 1)
        ]
        sanitized = self._sanitize_places(area, "activity", candidates)

        if len(sanitized) < MIN_ACTIVITY_CANDIDATES:
            fallback_candidates = await self._collect_activity_fallback_places(
                area=area,
                time_slot=time_slot,
                display=max(8, display // 2),
                start_rank=len(candidates) + 1,
            )
            sanitized = self._sanitize_places(area, "activity", candidates + fallback_candidates)
            logger.info(
                "recommendation.activity_fallback area=%s time_slot=%s fetched=%s sanitized=%s target=%s",
                area,
                time_slot.value,
                len(fallback_candidates),
                len(sanitized),
                MIN_ACTIVITY_CANDIDATES,
            )

        diversified = self._diversify_places(sanitized)
        logger.info(
            "recommendation.category_pool area=%s category=%s time_slot=%s raw=%s sanitized=%s diversified=%s samples=%s subtypes=%s",
            area,
            "activity",
            time_slot.value,
            len(raw),
            len(sanitized),
            len(diversified),
            self._sample_place_names(diversified),
            self._sample_activity_subtypes(diversified),
        )
        return diversified

    async def _collect_activity_fallback_places(
        self,
        area: str,
        time_slot: TimeSlot,
        display: int,
        start_rank: int,
    ) -> list[dict]:
        raw: list[tuple[dict, str]] = []
        subtype_keywords = ACTIVITY_SUBTYPE_FALLBACK_SEARCH_KEYWORDS.get(time_slot.value, {})
        for subtype, keywords in subtype_keywords.items():
            for kw in keywords:
                query = f"{area} {kw}"
                items = await self._search_places_cached(query, "activity", display)
                raw.extend((item, subtype) for item in items)
                self._log_collection_query(
                    area=area,
                    category="activity",
                    query=query,
                    fetched_count=len(items),
                    accumulated_count=len(raw),
                    sanitized_count=len(raw),
                    target_count=MIN_ACTIVITY_CANDIDATES,
                    subtype=subtype,
                )
                if len(raw) >= MIN_ACTIVITY_CANDIDATES:
                    break
            if len(raw) >= MIN_ACTIVITY_CANDIDATES:
                break
        return [
            self._to_place(item, "activity", rank, subtype_hint=subtype)
            for rank, (item, subtype) in enumerate(raw, start_rank)
        ]

    async def _search_places_cached(
        self,
        query: str,
        category: str,
        display: int,
    ) -> list[dict]:
        cache_key = (query, category, display)
        cached = self._place_search_cache.get(cache_key)
        if cached is not None:
            return cached

        items = await self._search.search_places(query, category, display=display)
        self._place_search_cache[cache_key] = items
        return items

    def _to_place(self, item: dict, category: str, rank: int, subtype_hint: str | None = None) -> Place:
        name = _BOLD_RE.sub("", html.unescape(item.get("title", "")))
        desc = html.unescape(item.get("description", ""))
        road_addr = item.get("roadAddress", "")
        area_name = road_addr.split(" ")[1] if len(road_addr.split(" ")) > 1 else road_addr.split(" ")[0]

        # mapx/mapy: WGS84 × 10^7
        lat = int(item.get("mapy", 0)) / 1e7
        lng = int(item.get("mapx", 0)) / 1e7

        raw_category = item.get("category", "")
        keywords = [k.strip() for k in raw_category.split(">") if k.strip()]

        has_parking = "주차" in desc or "주차" in raw_category

        brand = self._extract_brand(name)
        activity_subtype = self._infer_activity_subtype(
            name=name,
            description=desc,
            keywords=keywords,
            subtype_hint=subtype_hint,
        )
        return Place(
            name=name,
            area=area_name,
            category=category,
            address=item.get("address", ""),
            road_address=road_addr,
            latitude=lat,
            longitude=lng,
            search_rank=rank,
            keywords=keywords,
            activity_subtype=activity_subtype,
            main_description=desc,
            brief_description=desc[:60] if desc else "",
            telephone=item.get("telephone", ""),
            has_parking=has_parking,
            is_franchise=(brand in _MAJOR_FRANCHISE),
        )

    def _infer_activity_subtype(
        self,
        name: str,
        description: str,
        keywords: list[str],
        subtype_hint: str | None,
    ) -> str | None:
        if subtype_hint is None:
            return None

        text = self._normalize_text(" ".join([name, description, " ".join(keywords)]))
        for subtype, signals in ACTIVITY_SUBTYPE_SIGNALS.items():
            if any(self._normalize_text(signal) in text for signal in signals):
                return subtype
        return subtype_hint

    def _sanitize_places(self, requested_area: str, category: str, places: list[Place]) -> list[Place]:
        sanitized: list[Place] = []
        seen_keys: set[tuple[str, str]] = set()
        dropped_counts = {
            "invalid_coordinate": 0,
            "area_mismatch": 0,
            "duplicate": 0,
            "category_mismatch": 0,
        }

        for place in places:
            if not self._has_valid_coordinates(place):
                dropped_counts["invalid_coordinate"] += 1
                continue

            if not self._matches_requested_area(requested_area, place):
                dropped_counts["area_mismatch"] += 1
                continue

            dedupe_key = self._place_dedupe_key(place)
            if dedupe_key in seen_keys:
                dropped_counts["duplicate"] += 1
                continue

            if not self._matches_category_signal(category, place):
                dropped_counts["category_mismatch"] += 1
                continue

            seen_keys.add(dedupe_key)
            sanitized.append(place)

        if any(dropped_counts.values()):
            logger.info(
                "recommendation.sanitize area=%s category=%s before=%s after=%s dropped=%s",
                requested_area,
                category,
                len(places),
                len(sanitized),
                dropped_counts,
            )

        return sanitized

    def _diversify_places(self, places: list[Place]) -> list[Place]:
        ordered = [p for p in places if not p.is_franchise] + [p for p in places if p.is_franchise]
        brand_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        result: list[Place] = []
        for place in ordered:
            brand = self._extract_brand(place.name)
            place_type = place.keywords[-1] if place.keywords else ""
            if brand_counts.get(brand, 0) >= _BRAND_CAP:
                continue
            if place_type and type_counts.get(place_type, 0) >= _KEYWORD_TYPE_CAP:
                continue
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
            if place_type:
                type_counts[place_type] = type_counts.get(place_type, 0) + 1
            result.append(place)
        return result

    def _extract_brand(self, name: str) -> str:
        parts = name.split()
        if len(parts) > 1 and any(parts[-1].endswith(s) for s in ("점", "지점", "본점", "직영점")):
            return " ".join(parts[:-1])
        return name

    def _has_valid_coordinates(self, place: Place) -> bool:
        return not (
            abs(place.latitude) < 0.000001
            or abs(place.longitude) < 0.000001
            or not (-90 <= place.latitude <= 90)
            or not (-180 <= place.longitude <= 180)
        )

    def _matches_requested_area(self, requested_area: str, place: Place) -> bool:
        normalized_area = self._normalize_text(requested_area)
        if not normalized_area:
            return True

        haystack = self._normalize_text(
            " ".join(
                part
                for part in [place.name, place.area, place.address, place.road_address]
                if part
            )
        )
        if not haystack:
            return False

        if self._should_relax_area_matching(normalized_area):
            return normalized_area in haystack

        return all(token in haystack for token in normalized_area.split())

    def _should_relax_area_matching(self, normalized_area: str) -> bool:
        tokens = normalized_area.split()
        if not tokens:
            return True

        if normalized_area in {"서울", "서울시"}:
            return True

        if len(tokens) == 1:
            token = tokens[0]
            administrative_suffixes = ("시", "도", "구", "군", "동", "읍", "면", "리", "가")
            if not token.endswith(administrative_suffixes):
                return True

        return False

    def _place_dedupe_key(self, place: Place) -> tuple[str, str]:
        normalized_name = self._normalize_text(place.name)
        normalized_address = self._normalize_text(place.road_address or place.address)
        return normalized_name, normalized_address

    def _matches_category_signal(self, category: str, place: Place) -> bool:
        if category == "activity":
            return True
        signals = _CATEGORY_SIGNALS.get(category, ())
        if not signals:
            return True

        text = self._normalize_text(
            " ".join(
                [
                    place.name,
                    place.main_description,
                    place.brief_description,
                    " ".join(place.keywords),
                ]
            )
        )
        if not text:
            return True

        if any(signal in text for signal in signals):
            return True

        # 음식점은 카테고리 폭이 넓어서 너무 공격적으로 제외하지 않는다.
        if category == "restaurant":
            return True

        return False

    def _normalize_text(self, value: str) -> str:
        return " ".join(value.lower().split())

    def _sample_place_names(self, places: list[Place], limit: int = 5) -> list[str]:
        return [place.name for place in places[:limit]]

    def _sample_activity_subtypes(self, places: list[Place], limit: int = 5) -> list[str]:
        return [place.activity_subtype or "unknown" for place in places[:limit]]

    def _log_collection_query(
        self,
        area: str,
        category: str,
        query: str,
        fetched_count: int,
        accumulated_count: int,
        sanitized_count: int,
        target_count: int,
        subtype: str | None = None,
    ) -> None:
        logger.info(
            "recommendation.collect_query area=%s category=%s subtype=%s query=%s fetched=%s accumulated=%s sanitized=%s target=%s",
            area,
            category,
            subtype,
            query,
            fetched_count,
            accumulated_count,
            sanitized_count,
            target_count,
        )

    # ── 이미지 ────────────────────────────────────────────────────────────────

    async def _fetch_image(self, place: Place, category: str) -> str | None:
        cache_key = (place.name, place.area, category)
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        if self._image_lookup_rate_limited:
            logger.info(
                "recommendation.image_skipped place=%s category=%s reason=rate_limited",
                place.name,
                category,
            )
            self._image_cache[cache_key] = None
            return None

        if self._image_lookup_count >= _IMAGE_LOOKUP_LIMIT_PER_REQUEST:
            logger.info(
                "recommendation.image_skipped place=%s category=%s reason=budget_exceeded budget=%s",
                place.name,
                category,
                _IMAGE_LOOKUP_LIMIT_PER_REQUEST,
            )
            self._image_cache[cache_key] = None
            return None

        suffix = self._image_suffix_for_place(place, category)
        query = f"{place.area} {place.name} {suffix}"
        self._image_lookup_count += 1
        try:
            images = await self._search.search_images(query, display=3)
        except Exception as exc:
            if "429" in str(exc):
                self._image_lookup_rate_limited = True
            logger.warning(
                "recommendation.image_lookup_failed category=%s place=%s query=%s error=%s",
                category,
                place.name,
                query,
                exc,
            )
            self._image_cache[cache_key] = None
            return None
        best_url: str | None = None
        best_score: int | None = None
        for img in images:
            score = self._score_image_candidate(img, place, category)
            if score is None:
                continue
            image_url = img.get("link") or img.get("thumbnail")
            if not image_url:
                continue
            if best_score is None or score > best_score:
                best_score = score
                best_url = image_url
        if best_url is None:
            logger.info(
                "recommendation.image_missing place=%s category=%s query=%s candidates=%s",
                place.name,
                category,
                query,
                len(images),
            )
        self._image_cache[cache_key] = best_url
        return best_url

    def _is_valid_image(self, img: dict) -> bool:
        title = html.unescape(img.get("title", "")).lower()
        return not any(kw in title for kw in _IMAGE_EXCLUDE_KEYWORDS)

    def _score_image_candidate(self, img: dict, place: Place, category: str) -> int | None:
        title = self._normalize_text(html.unescape(img.get("title", "")))
        link = self._normalize_text(img.get("link", ""))
        combined = f"{title} {link}".strip()

        if not combined:
            return None
        if not self._is_valid_image(img):
            return None
        if any(keyword in combined for keyword in _IMAGE_HARD_EXCLUDE_KEYWORDS):
            return None
        if any(keyword in combined for keyword in _IMAGE_STOCK_EXCLUDE_KEYWORDS):
            return None
        if any(keyword in combined for keyword in _IMAGE_SOURCE_EXCLUDE_KEYWORDS):
            return None
        if any(keyword in combined for keyword in _IMAGE_MENU_EXCLUDE_KEYWORDS):
            return None

        score = 0
        place_name = self._normalize_text(place.name)
        area = self._normalize_text(place.area)
        exact_name_match = bool(place_name and place_name in combined)

        if exact_name_match:
            score += 6
        else:
            name_tokens = [token for token in place_name.split() if len(token) >= 2]
            score += sum(2 for token in name_tokens if token in combined)

        if area and area in combined:
            score += 2
        if any(keyword in combined for keyword in _IMAGE_PREFERRED_SOURCE_KEYWORDS):
            score += 2

        category_signals = _CATEGORY_SIGNALS.get(category, ())
        score += sum(1 for signal in category_signals if self._normalize_text(signal) in combined)
        score += self._activity_image_bonus(place, combined)

        if category in {"restaurant", "cafe"} and not exact_name_match:
            return None

        if any(bad in combined for bad in ("face", "selfie", "profile", "人物")):
            score -= 4

        if any(keyword in combined for keyword in _IMAGE_PEOPLE_EXCLUDE_KEYWORDS):
            score -= 8
        if category in {"restaurant", "cafe"} and any(
            keyword in combined for keyword in _IMAGE_SCENIC_EXCLUDE_KEYWORDS
        ):
            score -= 6

        minimum_score = 5 if category == "activity" else 7
        return score if score >= minimum_score else None

    def _image_suffix_for_place(self, place: Place, category: str) -> str:
        if category == "activity" and place.activity_subtype:
            return ACTIVITY_SUBTYPE_IMAGE_SUFFIX.get(place.activity_subtype, CATEGORY_IMAGE_SUFFIX[category])
        return CATEGORY_IMAGE_SUFFIX[category]

    def _activity_image_bonus(self, place: Place, combined: str) -> int:
        if place.category != "activity" or not place.activity_subtype:
            return 0

        subtype_signals = {
            "culture": ("전시", "갤러리", "미술관", "전시장"),
            "experience": ("체험", "공방", "클래스", "공간"),
            "walk": ("산책", "공원", "야경", "루프탑"),
            "nightlife": ("와인바", "칵테일", "바", "라운지"),
            "shopping": ("쇼룸", "편집숍", "소품샵", "매장"),
        }
        return sum(
            2
            for signal in subtype_signals.get(place.activity_subtype, ())
            if self._normalize_text(signal) in combined
        )

    # ── 지도 API 동선 보강 ─────────────────────────────────────────────────────

    async def _enrich_with_routes(self, courses: list[Course], transport: str) -> None:
        """랭킹된 최종 코스에 한해 Naver 지도 API로 실제 이동소요시간·경로 적용"""
        for course in courses:
            for i, cp in enumerate(course.places[:-1]):
                next_cp = course.places[i + 1]
                route = await self._map.get_directions(
                    cp.place.latitude, cp.place.longitude,
                    next_cp.place.latitude, next_cp.place.longitude,
                    transport,
                )
                if route is not None:
                    cp.travel_time_to_next_minutes = route.duration_minutes
                    cp.route_path_to_next = route.path

    # ── 응답 변환 ─────────────────────────────────────────────────────────────

    def _build_response(
        self,
        main: Course | None,
        sub1: Course | None,
        sub2: Course | None,
        region: str,
        time_slot: TimeSlot,
        total_courses: int,
        recommendation_id: str,
    ) -> CreateCourseResponseDto:
        message = _INSUFFICIENT_MESSAGE if total_courses < 3 else None
        used_cover_urls: set[str] = set()
        used_cover_categories: set[str] = set()
        used_title_axes: set[str] = set()
        used_title_phrases: set[str] = set()
        main_course = (
            self._to_course_dto(
                main,
                region,
                time_slot,
                str(uuid.uuid4()),
                used_cover_urls,
                used_cover_categories,
                used_title_axes,
                used_title_phrases,
            )
            if main
            else None
        )
        sub_courses = [
            self._to_course_dto(
                c,
                region,
                time_slot,
                str(uuid.uuid4()),
                used_cover_urls,
                used_cover_categories,
                used_title_axes,
                used_title_phrases,
            )
            for c in [sub1, sub2]
            if c is not None
        ]
        return CreateCourseResponseDto(
            course_id=recommendation_id,
            main_course=main_course,
            sub_courses=sub_courses,
            message=message,
        )

    def _to_course_dto(
        self,
        course: Course,
        region: str,
        time_slot: TimeSlot,
        course_id: str,
        used_cover_urls: set[str] | None = None,
        used_cover_categories: set[str] | None = None,
        used_title_axes: set[str] | None = None,
        used_title_phrases: set[str] | None = None,
    ) -> CourseResultDto:
        places = [
            PlaceResultDto(
                visit_order=cp.visit_order,
                name=cp.place.name,
                area=cp.place.area,
                category=cp.place.category,
                image_url=cp.place.image_url,
                main_description=cp.place.main_description,
                brief_description=cp.place.brief_description,
                keywords=[f"#{k}" for k in cp.place.keywords],
                estimated_duration_minutes=cp.estimated_duration_minutes,
                travel_time_to_next_minutes=cp.travel_time_to_next_minutes,
                recommended_time_slot=time_slot.value,
                has_parking=cp.place.has_parking if course.transport == "car" else None,
                route_path_to_next=cp.route_path_to_next,
            )
            for cp in course.places
        ]
        image_url, image_category = self._select_course_cover_image_v2(
            course,
            used_cover_urls or set(),
            used_cover_categories or set(),
        )
        if image_url and used_cover_urls is not None:
            used_cover_urls.add(image_url)
        if image_category and used_cover_categories is not None:
            used_cover_categories.add(image_category)
        main_place = self._select_title_lead_place(course, used_title_axes, used_title_phrases)
        main_title_axis = self._build_place_title_axis(main_place)
        main_title_phrase = self._build_place_title_phrase(main_place)
        if main_title_axis and used_title_axes is not None:
            used_title_axes.add(main_title_axis)
        if main_title_phrase and used_title_phrases is not None:
            used_title_phrases.add(main_title_phrase)
        return CourseResultDto(
            course_id=course_id,
            course_type=course.course_type,
            transport=course.transport,
            total_duration_minutes=course.total_duration_minutes(),
            region=region,
            main_place=self._to_title_place_dto(main_place),
            sub_places=self._build_sub_place_dtos(course, main_place),
            title=self._build_course_title_v2(course, time_slot, main_place),
            description=self._build_course_description(course, time_slot),
            image_url=image_url,
            places=places,
        )

    def _build_sub_place_dtos(
        self,
        course: Course,
        main_place: Place | None,
    ) -> list[CourseTitlePlaceDto]:
        title_places: list[CourseTitlePlaceDto] = []
        seen: set[tuple[str, str, str]] = set()
        main_category = main_place.category if main_place is not None else None
        main_title_key = self._build_place_title_keyword(main_place)

        candidates = sorted(
            (cp.place for cp in course.places if main_place is None or cp.place.name != main_place.name),
            key=lambda place: (
                place.category != main_category,
                self._build_place_title_keyword(place) != main_title_key,
                self._title_place_priority(place),
                place.score,
            ),
            reverse=True,
        )

        for place in candidates:
            title_place = self._to_title_place_dto(place)
            key = (title_place.name, title_place.category, title_place.sub_category)
            if key in seen:
                continue
            seen.add(key)
            title_places.append(title_place)

        return title_places

    def _to_title_place_dto(self, place: Place | None) -> CourseTitlePlaceDto | None:
        if place is None:
            return None

        return CourseTitlePlaceDto(
            name=place.name,
            category=place.category,
            sub_category=self._build_place_title_keyword(place),
        )

    def _build_course_title(self, course: Course, time_slot: TimeSlot) -> str:
        area = course.places[0].place.area if course.places else ""
        category_labels = {
            "restaurant": "맛집",
            "cafe": "카페",
            "activity": "데이트",
            "walk": "산책",
        }

        ordered_categories: list[str] = []
        for cp in course.places:
            category = cp.place.category
            if category not in ordered_categories:
                ordered_categories.append(category)

        labels = [category_labels.get(category, category) for category in ordered_categories[:2]]
        time_prefix_map = {
            "morning": "브런치",
            "lunch": "점심",
            "afternoon": "오후",
            "evening": "저녁",
            "late_night": "심야",
        }
        time_prefix = time_prefix_map.get(time_slot.value, "")

        if len(labels) >= 2:
            body = f"{labels[0]}와 {labels[1]} 코스"
        elif labels:
            body = f"{labels[0]} 데이트"
        else:
            body = "데이트 코스"

        if time_prefix and labels:
            body = f"{time_prefix} {body}"

        return f"{area} {body}".strip()

    def _build_course_description(self, course: Course, time_slot: TimeSlot) -> str:
        segments = [
            self._describe_course_place(cp.place.category, cp.place.keywords, cp.place.activity_subtype)
            for cp in course.places
        ]
        segments = [segment for segment in segments if segment]

        time_context = {
            "morning": "가볍게 시작하는",
            "lunch": "여유롭게 즐기는",
            "afternoon": "오후에 즐기는",
            "evening": "저녁에 즐기는",
            "late_night": "심야까지 이어지는",
        }.get(time_slot.value, "즐기는")

        if len(segments) >= 3:
            return f"{segments[0]}, {segments[1]}, {segments[2]} {time_context} 데이트 코스입니다."
        if len(segments) == 2:
            return f"{segments[0]}고 {segments[1]}는 {time_context} 데이트 코스입니다."
        if len(segments) == 1:
            return f"{segments[0]} 중심으로 구성한 {time_context} 데이트 코스입니다."
        return f"{time_context} 데이트 코스입니다."

    def _describe_course_place(
        self,
        category: str,
        keywords: list[str],
        activity_subtype: str | None = None,
    ) -> str:
        text = self._normalize_text(" ".join(keywords))

        if category == "restaurant":
            if "브런치" in text or "조식" in text:
                return "브런치를 즐기"
            if "이자카야" in text or "술집" in text or "포차" in text:
                return "식사와 한잔을 즐기"
            return "맛집에서 식사하"

        if category == "cafe":
            if "와인바" in text or "칵테일바" in text or "바" in text:
                return "와인바에서 분위기를 이어가"
            if "디저트" in text:
                return "디저트 카페에서 쉬"
            return "감성 카페에서 쉬"

        if activity_subtype == "culture":
            return "전시와 문화를 즐기"
        if activity_subtype == "experience":
            return "체험 데이트를 즐기"
        if activity_subtype == "walk":
            return "산책과 풍경을 즐기"
        if activity_subtype == "nightlife":
            return "밤 분위기를 즐기"
        if activity_subtype == "shopping":
            return "쇼핑과 구경을 즐기"

        if any(keyword in text for keyword in ("전시", "갤러리", "미술관", "박물관")):
            return "전시를 즐기"
        if any(keyword in text for keyword in ("공원", "산책", "루프탑", "야경")):
            return "산책을 즐기"
        if any(keyword in text for keyword in ("영화", "자동차극장")):
            return "영화를 즐기"
        if any(keyword in text for keyword in ("공방", "원데이", "도자기", "향수")):
            return "체험을 즐기"
        if any(keyword in text for keyword in ("볼링", "방탈출", "클라이밍", "보드게임")):
            return "액티브 데이트를 즐기"
        if any(keyword in text for keyword in ("편집숍", "소품샵", "빈티지", "쇼핑몰", "시장")):
            return "쇼핑을 즐기"
        if any(keyword in text for keyword in ("와인바", "칵테일바", "lp바", "루프탑바", "펍", "주점")):
            return "밤 분위기를 즐기"
        return "데이트를 즐기"

    def _select_course_cover_image(self, course: Course) -> str | None:
        ranked_candidates: list[tuple[int, str]] = []
        has_food_or_cafe = any(cp.place.category in {"restaurant", "cafe"} for cp in course.places)

        for cp in course.places:
            image_url = cp.place.image_url
            if not image_url:
                continue

            score = 6
            if cp.place.category == "restaurant":
                score = 12
            elif cp.place.category == "cafe":
                score = 10

            combined = self._normalize_text(
                " ".join([image_url, cp.place.name, cp.place.main_description, " ".join(cp.place.keywords)])
            )
            if any(keyword in combined for keyword in _IMAGE_STOCK_EXCLUDE_KEYWORDS):
                score -= 10
            if any(keyword in combined for keyword in _IMAGE_PEOPLE_EXCLUDE_KEYWORDS):
                score -= 8
            if has_food_or_cafe and cp.place.category == "activity" and any(
                keyword in combined for keyword in _IMAGE_SCENIC_EXCLUDE_KEYWORDS
            ):
                score -= 10

            ranked_candidates.append((score, image_url))

        if not ranked_candidates:
            return None

        ranked_candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_url = ranked_candidates[0]
        return best_url if best_score > 0 else None

    # ── 유틸 ──────────────────────────────────────────────────────────────────

    def _build_course_title_v2(
        self,
        course: Course,
        time_slot: TimeSlot,
        lead_place: Place | None = None,
    ) -> str:
        lead_place = lead_place or self._select_title_lead_place(course)
        secondary_place = self._select_title_secondary_place(course, lead_place)
        return self._build_course_mood_title(course, time_slot, lead_place, secondary_place)

    def _build_course_mood_title(
        self,
        course: Course,
        time_slot: TimeSlot,
        lead_place: Place | None,
        secondary_place: Place | None,
    ) -> str:
        primary_place = lead_place or self._select_title_lead_place(course)
        if primary_place is None:
            return self._default_time_title(time_slot)

        primary_label = self._build_title_label(primary_place)
        primary_axis = self._build_place_title_axis(primary_place)
        primary_role = self._build_title_role(primary_axis)

        secondary_candidate = secondary_place or self._select_title_secondary_place(course, primary_place)
        secondary_role_order = self._preferred_secondary_roles(primary_role)
        secondary_point = self._select_title_point(course, primary_place, secondary_role_order, secondary_candidate)

        if secondary_point is not None:
            secondary_label = self._build_title_label(secondary_point)
            secondary_axis = self._build_place_title_axis(secondary_point)
            secondary_role = self._build_title_role(secondary_axis)
            title = self._compose_role_based_title(
                primary_label,
                primary_axis,
                primary_role,
                secondary_label,
                secondary_axis,
                secondary_role,
            )
            if title:
                return title

        fallback = self._compose_single_point_title(primary_label, primary_axis, primary_role, time_slot)
        return fallback or self._default_time_title(time_slot)

    def _select_title_point(
        self,
        course: Course,
        primary_place: Place,
        preferred_roles: tuple[str, ...],
        secondary_candidate: Place | None = None,
    ) -> Place | None:
        candidates = [cp.place for cp in course.places if cp.place.name != primary_place.name]
        if secondary_candidate is not None and secondary_candidate.name != primary_place.name:
            candidates = [secondary_candidate] + [
                place for place in candidates if place.name != secondary_candidate.name
            ]

        if not candidates:
            return None

        for role in preferred_roles:
            matched = [
                place
                for place in candidates
                if self._build_title_role(self._build_place_title_axis(place)) == role
            ]
            if matched:
                return max(matched, key=lambda place: (self._title_place_priority(place), place.score))
        return max(candidates, key=lambda place: (self._title_place_priority(place), place.score))

    def _preferred_secondary_roles(self, primary_role: str) -> tuple[str, ...]:
        mapping = {
            "meal": ("rest", "activity", "finish", "meal", "other"),
            "rest": ("activity", "meal", "finish", "rest", "other"),
            "activity": ("rest", "meal", "finish", "activity", "other"),
            "finish": ("rest", "meal", "activity", "finish", "other"),
        }
        return mapping.get(primary_role, ("rest", "activity", "meal", "finish", "other"))

    def _compose_role_based_title(
        self,
        primary_label: str,
        primary_axis: str,
        primary_role: str,
        secondary_label: str,
        secondary_axis: str,
        secondary_role: str,
    ) -> str:
        if primary_role == "meal" and secondary_role == "rest":
            return self._pick_title_variant(
                (
                    f"{primary_label} 먹고 {secondary_label}로 마무리",
                    f"{primary_label} 다음은 {secondary_label}, 밸런스 좋은 데이트",
                    f"{primary_label}부터 {secondary_label}까지 이어지는 코스",
                ),
                primary_label,
                secondary_label,
                primary_role,
                secondary_role,
            )
        if primary_role == "meal" and secondary_role == "activity":
            return self._pick_title_variant(
                (
                    f"{primary_label} 먹고 {secondary_label}까지",
                    f"{primary_label} 다음은 {secondary_label}, 심심할 틈 없는 코스",
                    f"{primary_label} 즐긴 뒤 {secondary_label}까지 이어가기",
                ),
                primary_label,
                secondary_label,
                primary_role,
                secondary_role,
            )
        if primary_role == "rest" and secondary_role == "activity":
            return self._pick_title_variant(
                (
                    f"{primary_label} 들른 뒤 {secondary_label}까지",
                    f"{primary_label}로 예열하고 {secondary_label}까지 가는 코스",
                    f"{primary_label} 한 번 들르고 {secondary_label}까지 이어가기",
                ),
                primary_label,
                secondary_label,
                primary_role,
                secondary_role,
            )
        if primary_role == "rest" and secondary_role == "meal":
            return self._pick_title_variant(
                (
                    f"{primary_label} 들르고 {secondary_label}까지",
                    f"{primary_label}로 시작해 {secondary_label}까지 이어지는 코스",
                    f"{primary_label} 챙기고 {secondary_label}까지 가는 데이트",
                ),
                primary_label,
                secondary_label,
                primary_role,
                secondary_role,
            )
        if primary_role == "activity" and secondary_role == "rest":
            return self._pick_title_variant(
                (
                    f"{primary_label}{self._activity_joiner(primary_axis)} {secondary_label}로 쉬어가는 코스",
                    f"{primary_label}{self._activity_joiner(primary_axis)} {secondary_label}에서 한숨 돌리기",
                    f"{primary_label}{self._activity_joiner(primary_axis)} {secondary_label}로 여운 잇기",
                ),
                primary_label,
                secondary_label,
                primary_axis,
                primary_role,
                secondary_role,
            )
        if primary_role == "activity" and secondary_role == "meal":
            return self._pick_title_variant(
                (
                    f"{primary_label}{self._activity_joiner(primary_axis)} {secondary_label}까지",
                    f"{primary_label}{self._activity_joiner(primary_axis)} {secondary_label}로 배 채우기",
                    f"{primary_label}{self._activity_joiner(primary_axis)} {secondary_label}까지 이어지는 코스",
                ),
                primary_label,
                secondary_label,
                primary_axis,
                primary_role,
                secondary_role,
            )
        if primary_role == "finish" and secondary_role == "rest":
            return self._pick_title_variant(
                (
                    f"{primary_label} 즐기고 {secondary_label}로 마무리",
                    f"{primary_label} 뒤엔 {secondary_label}, 밤 분위기 살리는 코스",
                    f"{primary_label} 즐긴 다음 {secondary_label}에서 여운 남기기",
                ),
                primary_label,
                secondary_label,
                primary_role,
                secondary_role,
            )
        if primary_role == "finish" and secondary_role == "meal":
            return self._pick_title_variant(
                (
                    f"{primary_label} 즐기고 {secondary_label}까지",
                    f"{primary_label} 뒤에 {secondary_label}까지 챙기는 코스",
                    f"{primary_label} 즐긴 다음 {secondary_label}까지 이어가기",
                ),
                primary_label,
                secondary_label,
                primary_role,
                secondary_role,
            )
        if secondary_role == "finish":
            return self._pick_title_variant(
                (
                    f"{primary_label}{self._flow_joiner(primary_role, primary_axis)} {secondary_label}로 마무리",
                    f"{primary_label}{self._flow_joiner(primary_role, primary_axis)} 마지막은 {secondary_label}",
                    f"{primary_label}{self._flow_joiner(primary_role, primary_axis)} {secondary_label}까지 가는 코스",
                ),
                primary_label,
                secondary_label,
                primary_axis,
                primary_role,
                secondary_role,
            )
        return self._pick_title_variant(
            (
                f"{primary_label}{self._flow_joiner(primary_role, primary_axis)} {secondary_label}까지",
                f"{primary_label}{self._flow_joiner(primary_role, primary_axis)} {secondary_label}로 이어지는 데이트",
                f"{primary_label}{self._flow_joiner(primary_role, primary_axis)} {secondary_label}까지 가볍게 즐기기",
            ),
            primary_label,
            secondary_label,
            primary_axis,
            secondary_axis,
            primary_role,
            secondary_role,
        )

    def _compose_single_point_title(
        self,
        primary_label: str,
        primary_axis: str,
        primary_role: str,
        time_slot: TimeSlot,
    ) -> str:
        if primary_role == "meal":
            return self._pick_title_variant(
                (
                    f"{primary_label} 먹고 쉬어가는 코스",
                    f"{primary_label} 중심으로 가볍게 즐기는 코스",
                    f"{primary_label} 하나로 기분 내기 좋은 코스",
                ),
                primary_label,
                primary_axis,
                primary_role,
                time_slot.value,
            )
        if primary_role == "rest":
            return self._pick_title_variant(
                (
                    f"{primary_label} 들르기 좋은 {self._slot_time_phrase(time_slot)}",
                    f"{primary_label}에서 여유 보내기 좋은 {self._slot_time_phrase(time_slot)}",
                    f"{primary_label} 하나로 완성되는 {self._slot_time_phrase(time_slot)}",
                ),
                primary_label,
                primary_axis,
                primary_role,
                time_slot.value,
            )
        if primary_role == "activity":
            return self._pick_title_variant(
                (
                    f"{primary_label}{self._activity_joiner(primary_axis)} {self._slot_mood_phrase(time_slot)} 코스",
                    f"{primary_label} 하나로 분위기 나는 {self._slot_time_phrase(time_slot)}",
                    f"{primary_label} 즐기러 가기 좋은 {self._slot_time_phrase(time_slot)}",
                ),
                primary_label,
                primary_axis,
                primary_role,
                time_slot.value,
            )
        if primary_role == "finish":
            return self._pick_title_variant(
                (
                    f"{primary_label} 즐기기 좋은 {self._slot_finish_phrase(time_slot)}",
                    f"{primary_label}로 끝내기 좋은 {self._slot_finish_phrase(time_slot)}",
                    f"{primary_label}가 메인인 {self._slot_finish_phrase(time_slot)}",
                ),
                primary_label,
                primary_axis,
                primary_role,
                time_slot.value,
            )
        return f"{primary_label} 즐기기 좋은 코스"

    def _build_title_role(self, axis: str) -> str:
        role_map = {
            "food": "meal",
            "dessert": "rest",
            "cafe": "rest",
            "culture": "activity",
            "walk": "activity",
            "experience": "activity",
            "movie": "activity",
            "activity": "activity",
            "shopping": "activity",
            "night": "finish",
        }
        return role_map.get(axis, "other")

    def _build_title_label(self, place: Place | None) -> str:
        if place is None:
            return ""

        phrase = self._build_place_title_phrase(place)
        label_map = {
            "브런치": "브런치",
            "이자카야": "이자카야",
            "감자탕": "감자탕",
            "피자 맛집": "피자 맛집",
            "버거 맛집": "버거 맛집",
            "파스타 맛집": "파스타 맛집",
            "국밥 맛집": "국밥 맛집",
            "아시안 맛집": "아시안 맛집",
            "스시 맛집": "스시 맛집",
            "한식 맛집": "한식 맛집",
            "맛집": "맛집",
            "베이커리 카페": "베이커리",
            "디저트 카페": "디저트",
            "브런치 카페": "브런치 카페",
            "카페": "카페",
            "전시": "전시",
            "체험": "체험",
            "산책": "산책",
            "영화": "영화",
            "액티비티": "액티비티",
            "쇼핑": "쇼핑",
            "야경": "야경",
            "바": "바",
            "데이트": "데이트",
        }
        base_label = label_map.get(phrase, phrase)
        if phrase not in _GENERIC_TITLE_PHRASES:
            return base_label

        hint = self._build_place_hint(place)
        if not hint or hint in base_label:
            return base_label
        return f"{hint} {base_label}"

    def _pick_title_variant(self, candidates: tuple[str, ...], *keys: str) -> str:
        if not candidates:
            return ""

        seed = "".join(keys)
        if not seed:
            return candidates[0]

        index = sum(ord(char) for char in seed) % len(candidates)
        return candidates[index]

    def _activity_joiner(self, axis: str) -> str:
        if axis in {"culture", "movie"}:
            return " 보고"
        if axis == "walk":
            return "하고"
        if axis == "experience":
            return "하고"
        if axis == "shopping":
            return " 구경하고"
        return " 즐기고"

    def _flow_joiner(self, role: str, axis: str) -> str:
        if role == "meal":
            return " 먹고"
        if role == "rest":
            return " 들른 뒤"
        if role == "activity":
            return self._activity_joiner(axis)
        if role == "finish":
            return " 즐기고"
        return " 즐기고"

    def _slot_mood_phrase(self, time_slot: TimeSlot) -> str:
        mapping = {
            "morning": "가볍게 시작하는",
            "lunch": "여유로운",
            "afternoon": "오후에 쉬기 좋은",
            "evening": "저녁에 머물기 좋은",
            "late_night": "밤에 들르기 좋은",
        }
        return mapping.get(time_slot.value, "머물기 좋은")

    def _slot_time_phrase(self, time_slot: TimeSlot) -> str:
        mapping = {
            "morning": "아침 코스",
            "lunch": "점심 코스",
            "afternoon": "오후 코스",
            "evening": "저녁 코스",
            "late_night": "밤 코스",
        }
        return mapping.get(time_slot.value, "코스")

    def _slot_finish_phrase(self, time_slot: TimeSlot) -> str:
        mapping = {
            "morning": "아침 코스",
            "lunch": "점심 코스",
            "afternoon": "오후 코스",
            "evening": "저녁 코스",
            "late_night": "밤 코스",
        }
        return mapping.get(time_slot.value, "코스")

    def _select_title_lead_place(
        self,
        course: Course,
        used_title_axes: set[str] | None = None,
        used_title_phrases: set[str] | None = None,
    ) -> Place | None:
        ranked = sorted(
            (cp.place for cp in course.places),
            key=lambda place: (self._title_place_priority(place), place.score),
            reverse=True,
        )
        if not ranked:
            return None
        if used_title_phrases:
            unused_phrase = [
                place for place in ranked
                if self._build_place_title_phrase(place) not in used_title_phrases
            ]
            if unused_phrase:
                return unused_phrase[0]
        if used_title_axes:
            unused = [
                place for place in ranked
                if self._build_place_title_axis(place) not in used_title_axes
            ]
            if unused:
                return unused[0]
        return ranked[0]

    def _select_title_secondary_place(self, course: Course, lead_place: Place | None) -> Place | None:
        if lead_place is None:
            return None

        lead_title_axis = self._build_place_title_axis(lead_place)
        candidates = [cp.place for cp in course.places if cp.place.name != lead_place.name]
        differentiated = [
            place for place in candidates if self._build_place_title_axis(place) != lead_title_axis
        ]
        pool = differentiated or candidates
        if not pool:
            return None
        return max(pool, key=lambda place: (self._title_place_priority(place), place.score))

    def _build_place_title_block(self, place: Place) -> str:
        return self._build_place_title_keyword(place)

    def _build_place_title_phrase(self, place: Place | None) -> str:
        if place is None:
            return ""

        text = self._normalize_text(
            " ".join([place.name, place.main_description, place.brief_description, " ".join(place.keywords)])
        )

        if place.category == "restaurant":
            if "brunch" in text or "조식" in text:
                return "브런치"
            if "이자카야" in text or "포차" in text or "술집" in text:
                return "이자카야"
            if "감자탕" in text:
                return "감자탕"
            if "피자" in text:
                return "피자 맛집"
            if "버거" in text:
                return "버거 맛집"
            if any(keyword in text for keyword in ("파스타", "리조또")):
                return "파스타 맛집"
            if any(keyword in text for keyword in ("국밥", "해장국", "순대국")):
                return "국밥 맛집"
            if any(keyword in text for keyword in ("쌀국수", "분짜", "팟타이", "베트남")):
                return "아시안 맛집"
            if any(keyword in text for keyword in ("스시", "초밥", "오마카세")):
                return "스시 맛집"
            if any(keyword in text for keyword in ("한식", "백반", "한정식")):
                return "한식 맛집"
            return "맛집"

        if place.category == "cafe":
            if "와인바" in text or "칵테일바" in text or "lp바" in text:
                return "바"
            if "베이커리" in text:
                return "베이커리 카페"
            if "디저트" in text or "빙수" in text:
                return "디저트 카페"
            if "브런치" in text:
                return "브런치 카페"
            return "카페"

        if place.activity_subtype == "culture":
            return "전시"
        if place.activity_subtype == "experience":
            return "체험"
        if place.activity_subtype == "walk":
            return "산책"
        if place.activity_subtype == "nightlife":
            return "야경"
        if place.activity_subtype == "shopping":
            return "쇼핑"

        if any(keyword in text for keyword in ("전시", "갤러리", "미술관", "박물관")):
            return "전시"
        if any(keyword in text for keyword in ("공원", "산책", "루프탑", "야경")):
            return "산책"
        if any(keyword in text for keyword in ("영화", "자동차극장")):
            return "영화"
        if any(keyword in text for keyword in ("공방", "원데이", "도자기", "향수")):
            return "체험"
        if any(keyword in text for keyword in ("볼링", "방탈출", "클라이밍", "보드게임")):
            return "액티비티"
        if any(keyword in text for keyword in ("편집숍", "소품샵", "빈티지", "쇼핑몰", "시장")):
            return "쇼핑"
        if any(keyword in text for keyword in ("와인바", "칵테일바", "lp바", "루프탑바", "홀덤", "주점")):
            return "야경"
        return "데이트"

    def _build_place_title_keyword(self, place: Place | None) -> str:
        phrase = self._build_place_title_phrase(place)
        if place is None:
            return phrase

        hint = self._build_place_hint(place)
        if not hint:
            return phrase
        if phrase not in _GENERIC_TITLE_PHRASES:
            return phrase
        if hint in phrase:
            return phrase
        return f"{hint} {phrase}"

    def _build_place_title_axis(self, place: Place | None) -> str:
        phrase = self._build_place_title_phrase(place)
        axis_map = {
            "브런치": "food",
            "이자카야": "food",
            "감자탕": "food",
            "피자 맛집": "food",
            "버거 맛집": "food",
            "파스타 맛집": "food",
            "국밥 맛집": "food",
            "아시안 맛집": "food",
            "스시 맛집": "food",
            "한식 맛집": "food",
            "맛집": "food",
            "베이커리 카페": "dessert",
            "디저트 카페": "dessert",
            "브런치 카페": "cafe",
            "카페": "cafe",
            "전시": "culture",
            "체험": "experience",
            "산책": "walk",
            "영화": "movie",
            "액티비티": "activity",
            "쇼핑": "shopping",
            "야경": "night",
            "바": "night",
        }
        return axis_map.get(phrase, "other")

    def _build_place_hint(self, place: Place | None) -> str:
        if place is None:
            return ""

        name = re.sub(r"\s*\([^)]*\)", "", place.name).strip()
        if not name:
            return ""
        name = re.sub(r"\s+(본점|별관|1호점|2호점)$", "", name).strip()
        tokens = name.split()
        first_token = tokens[0]
        if self._is_major_franchise_hint(first_token):
            return first_token
        if len(tokens) >= 2 and len(name) > 8:
            return first_token[:8]
        if len(name) <= 8:
            return name
        return name[:8]

    def _is_major_franchise_hint(self, text: str) -> bool:
        return text in _MAJOR_FRANCHISE

    def _title_place_priority(self, place: Place) -> int:
        phrase = self._build_place_title_phrase(place)
        priority_map = {
            "전시": 10,
            "체험": 10,
            "영화": 9,
            "액티비티": 9,
            "산책": 8,
            "쇼핑": 8,
            "야경": 8,
            "베이커리 카페": 7,
            "디저트 카페": 7,
            "브런치 카페": 7,
            "브런치": 7,
            "이자카야": 7,
            "감자탕": 7,
            "바": 7,
            "피자 맛집": 6,
            "버거 맛집": 6,
            "파스타 맛집": 6,
            "국밥 맛집": 6,
            "아시안 맛집": 6,
            "스시 맛집": 6,
            "한식 맛집": 6,
            "카페": 5,
            "맛집": 5,
            "데이트": 4,
        }
        return priority_map.get(phrase, 4)

    def _default_time_title(self, time_slot: TimeSlot) -> str:
        default_map = {
            "morning": "아침 데이트 코스",
            "lunch": "점심 데이트 코스",
            "afternoon": "오후 데이트 코스",
            "evening": "저녁 데이트 코스",
            "late_night": "심야 데이트 코스",
        }
        return default_map.get(time_slot.value, "데이트 코스")


    def _select_course_cover_image_v2(
        self,
        course: Course,
        used_image_urls: set[str],
        used_image_categories: set[str],
    ) -> tuple[str | None, str | None]:
        ranked_candidates: list[tuple[int, str, str]] = []
        has_food_or_cafe = any(cp.place.category in {"restaurant", "cafe"} for cp in course.places)

        for cp in course.places:
            image_url = cp.place.image_url
            if not image_url:
                continue

            score = 6
            if cp.place.category == "restaurant":
                score = 14
            elif cp.place.category == "cafe":
                score = 12

            combined = self._normalize_text(
                " ".join([image_url, cp.place.name, cp.place.main_description, " ".join(cp.place.keywords)])
            )
            if any(keyword in combined for keyword in _IMAGE_STOCK_EXCLUDE_KEYWORDS):
                score -= 12
            if any(keyword in combined for keyword in _IMAGE_PEOPLE_EXCLUDE_KEYWORDS):
                score -= 12
            if has_food_or_cafe and cp.place.category == "activity" and any(
                keyword in combined for keyword in _IMAGE_SCENIC_EXCLUDE_KEYWORDS
            ):
                score -= 14
            if cp.place.category in used_image_categories:
                score -= 5
            if image_url in used_image_urls:
                score -= 10

            ranked_candidates.append((score, image_url, cp.place.category))

        if not ranked_candidates:
            return None, None

        ranked_candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_url, best_category = ranked_candidates[0]
        if best_score <= 0:
            return None, None
        return best_url, best_category

    def _log_recommendation_diagnostics(
        self,
        dto: CreateCourseRequestDto,
        time_slot: TimeSlot,
        transport: Transport,
        places_by_category: dict[str, list[Place]],
        filtered_places: dict[str, list[Place]],
        courses: list[Course],
    ) -> None:
        raw_counts = {category: len(places) for category, places in places_by_category.items()}
        filtered_counts = {category: len(places) for category, places in filtered_places.items()}
        empty_after_filter = [
            category for category, count in filtered_counts.items() if count == 0
        ]
        populated_categories = [
            category for category, count in filtered_counts.items() if count > 0
        ]

        if len(courses) >= 3:
            logger.info(
                "recommendation.generated area=%s time_slot=%s transport=%s raw_counts=%s filtered_counts=%s course_count=%s",
                dto.area,
                time_slot.value,
                transport.value,
                raw_counts,
                filtered_counts,
                len(courses),
            )
            return

        reason_codes: list[str] = []
        if not populated_categories:
            reason_codes.append("no_places_after_filter")
        elif len(populated_categories) == 1:
            reason_codes.append("single_category_remaining")
        elif len(courses) == 0:
            reason_codes.append("composition_failed")
        if len(courses) < 3:
            reason_codes.append("insufficient_course_count")
        if empty_after_filter:
            reason_codes.append("category_exhausted_after_filter")

        logger.warning(
            "recommendation.insufficient area=%s start_time=%s time_slot=%s transport=%s raw_counts=%s filtered_counts=%s empty_after_filter=%s populated_categories=%s course_count=%s reason_codes=%s",
            dto.area,
            dto.start_time,
            time_slot.value,
            transport.value,
            raw_counts,
            filtered_counts,
            empty_after_filter,
            populated_categories,
            len(courses),
            reason_codes,
        )

    def _parse_time(self, time_str: str) -> time:
        try:
            h, m = map(int, time_str.split(":"))
            return time(h, m)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"시간 형식이 올바르지 않습니다: {time_str}") from e
