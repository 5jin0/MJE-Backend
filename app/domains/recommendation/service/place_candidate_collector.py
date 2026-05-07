import asyncio
import concurrent.futures
import logging
import math
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from app.domains.recommendation.domain.value_object.place import Place
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.service.place_search_query_builder import (
    ActivityKind,
    PlaceSearchQuery,
    PlaceSearchQueryBuilder,
)
from app.domains.recommendation.service.search_client_interface import (
    RawPlaceResult,
    SearchClientInterface,
)

_MIN_REQUIRED = 5
_DISPLAY_PER_QUERY = 10
_FILTER_RADIUS_KM = 3.0
_ACTIVITY_MAX_RESULTS = 3
_SEARCH_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=20)
_KR_LON_RANGE = (124.0, 132.0)
_KR_LAT_RANGE = (33.0, 39.0)
_logger = logging.getLogger(__name__)

_CATEGORY_BLACKLIST = frozenset([
    "반려동물", "애견", "동물병원", "수의사",
    "병원", "의원", "약국", "한의원", "치과",
    "부동산", "공인중개", "법무사", "변호사", "세무",
    "주유소", "세차", "자동차",
    "편의점", "마트", "슈퍼마켓",
    "헬스", "피트니스", "필라테스", "요가",
])

_ACTIVITY_CAFE_EXCLUDE = frozenset(["카페", "커피"])

_RESTAURANT_CATEGORY_EXCLUDE = frozenset([
    "카페", "커피", "베이커리", "빵", "디저트",
])


def _is_blacklisted(category: str) -> bool:
    return any(bad in category for bad in _CATEGORY_BLACKLIST)


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _in_korea(lat: float, lon: float) -> bool:
    return _KR_LON_RANGE[0] <= lon <= _KR_LON_RANGE[1] and _KR_LAT_RANGE[0] <= lat <= _KR_LAT_RANGE[1]


def _filter_by_radius(places: List[Place], center: Tuple[float, float], radius_km: float) -> List[Place]:
    center_lon, center_lat = center
    result = []
    for place in places:
        if not _in_korea(place.latitude, place.longitude):
            result.append(place)
            continue
        if _haversine_km(place.longitude, place.latitude, center_lon, center_lat) <= radius_km:
            result.append(place)
    return result


def _place_score(search_rank: int) -> float:
    return max(0.05, 1.0 - (search_rank - 1) * 0.05)


def _to_place(raw: RawPlaceResult, query: PlaceSearchQuery, search_rank: int) -> Place:
    try:
        lat = float(raw.mapy) if raw.mapy else 0.0
        lon = float(raw.mapx) if raw.mapx else 0.0
    except (ValueError, TypeError):
        lat, lon = 0.0, 0.0

    road_addr = raw.road_address or ""
    addr = raw.address or ""
    tokens = road_addr.split() if road_addr else addr.split()
    area = tokens[1] if len(tokens) > 1 else (tokens[0] if tokens else "")

    keywords = [k.strip() for k in raw.category.split(">") if k.strip()]
    activity_type = query.activity_kind.activity_type.value if query.activity_kind else None

    place_key = f"{raw.title}|{road_addr or addr}"
    score = _place_score(search_rank)

    return Place(
        name=raw.title,
        area=area,
        category=query.place_type.value,
        address=addr,
        road_address=road_addr,
        latitude=lat,
        longitude=lon,
        search_rank=search_rank,
        keywords=keywords,
        activity_type=activity_type,
        score=score,
        place_key=place_key,
        link=raw.link,
        telephone=raw.telephone,
    )


@dataclass
class PlaceCandidateCollection:
    restaurants: List[Place]
    cafes: List[Place]
    activities: List[Place]
    shortage_reasons: List[str]


class PlaceCandidateCollector:
    def __init__(self, client: SearchClientInterface) -> None:
        self._client = client
        self._query_builder = PlaceSearchQueryBuilder()

    async def collect(
        self,
        area: str,
        center_coords: Optional[Tuple[float, float]] = None,
    ) -> PlaceCandidateCollection:
        _logger.info("[Collector] start: area=%r center_coords=%s", area, center_coords)
        loop = asyncio.get_running_loop()

        all_kinds = list(ActivityKind)
        results = await asyncio.gather(
            loop.run_in_executor(
                _SEARCH_EXECUTOR,
                self._collect_by_queries,
                self._query_builder.build_restaurant_queries(area),
                _MIN_REQUIRED,
            ),
            loop.run_in_executor(
                _SEARCH_EXECUTOR,
                self._collect_by_queries,
                self._query_builder.build_cafe_queries(area),
                _MIN_REQUIRED,
            ),
            *[
                loop.run_in_executor(
                    _SEARCH_EXECUTOR,
                    self._collect_by_queries,
                    self._query_builder.build_activity_queries_for_kind(area, kind),
                    _ACTIVITY_MAX_RESULTS,
                )
                for kind in all_kinds
            ],
        )

        restaurants: List[Place] = results[0]
        cafes: List[Place] = results[1]
        activities: List[Place] = [
            place
            for places in results[2:]
            for place in places
            if not _is_cafe_like_nonnightlife(place)
        ]

        if center_coords:
            restaurants = _filter_by_radius(restaurants, center_coords, _FILTER_RADIUS_KM)
            cafes = _filter_by_radius(cafes, center_coords, _FILTER_RADIUS_KM)
            activities = _filter_by_radius(activities, center_coords, _FILTER_RADIUS_KM)

        _logger.info(
            "[Collector] done: area=%r restaurants=%d cafes=%d activities=%d",
            area, len(restaurants), len(cafes), len(activities),
        )

        shortage_reasons: List[str] = []
        if len(restaurants) < _MIN_REQUIRED:
            shortage_reasons.append(
                f"식당 후보가 부족해요. 현재 {len(restaurants)}개만 찾았고 최소 {_MIN_REQUIRED}개가 필요해요."
            )
        if len(cafes) < _MIN_REQUIRED:
            shortage_reasons.append(
                f"카페 후보가 부족해요. 현재 {len(cafes)}개만 찾았고 최소 {_MIN_REQUIRED}개가 필요해요."
            )
        if len(activities) < _MIN_REQUIRED:
            shortage_reasons.append(
                f"활동 후보가 부족해요. 현재 {len(activities)}개만 찾았고 최소 {_MIN_REQUIRED}개가 필요해요."
            )

        return PlaceCandidateCollection(
            restaurants=restaurants,
            cafes=cafes,
            activities=activities,
            shortage_reasons=shortage_reasons,
        )

    def _collect_by_queries(
        self,
        queries: List[PlaceSearchQuery],
        max_results: int = _MIN_REQUIRED,
    ) -> List[Place]:
        seen: Set[str] = set()
        results: List[Place] = []

        for search_query in queries:
            if len(results) >= max_results:
                break
            try:
                raw_items = self._client.search_places(search_query.query, _DISPLAY_PER_QUERY)
            except Exception as e:
                _logger.error("[Collector] error: query=%r error=%r", search_query.query, str(e))
                continue

            for rank, raw in enumerate(raw_items, start=1):
                if len(results) >= max_results:
                    break
                if not (raw.road_address or raw.address):
                    continue
                if _is_blacklisted(raw.category):
                    continue
                if (
                    search_query.place_type == PlaceType.RESTAURANT
                    and any(kw in raw.category for kw in _RESTAURANT_CATEGORY_EXCLUDE)
                ):
                    continue

                place_key = f"{raw.title}|{raw.road_address or raw.address}"
                if place_key in seen:
                    continue
                seen.add(place_key)

                results.append(_to_place(raw, search_query, rank))

        return results


def _is_nightlife_type(activity_type: Optional[str]) -> bool:
    from app.domains.recommendation.domain.value_object.activity_type import ActivityType
    return activity_type == ActivityType.NIGHTLIFE.value


def _is_cafe_like_nonnightlife(place: Place) -> bool:
    if _is_nightlife_type(place.activity_type):
        return False
    category_text = " ".join(place.keywords)
    return any(kw in category_text for kw in _ACTIVITY_CAFE_EXCLUDE)
