import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Set, Tuple

from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace
from app.domains.recommendation.service.place_search_query_builder import (
    PlaceSearchQuery,
    PlaceSearchQueryBuilder,
)
from app.domains.recommendation.service.search_client_interface import SearchClientInterface

_MIN_REQUIRED = 5
_DISPLAY_PER_QUERY = 5
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    return _HTML_TAG_PATTERN.sub("", text).strip()


def _place_id(name: str, address: str) -> int:
    return abs(hash((name, address))) % (10**9)


@dataclass
class PlaceCandidateCollection:
    restaurants: List[CandidatePlace]
    cafes: List[CandidatePlace]
    activities: List[CandidatePlace]
    shortage_reasons: List[str]


class PlaceCandidateCollector:
    def __init__(self, client: SearchClientInterface) -> None:
        self._client = client
        self._query_builder = PlaceSearchQueryBuilder()

    async def collect(self, area: str) -> PlaceCandidateCollection:
        _logger.info("[Collector] start: area=%r", area)
        loop = asyncio.get_running_loop()

        restaurants, cafes, activities = await asyncio.gather(
            loop.run_in_executor(None, self._collect_by_queries, self._query_builder.build_restaurant_queries(area)),
            loop.run_in_executor(None, self._collect_by_queries, self._query_builder.build_cafe_queries(area)),
            loop.run_in_executor(None, self._collect_by_queries, self._query_builder.build_activity_queries(area)),
        )

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

    def _collect_by_queries(self, queries: List[PlaceSearchQuery]) -> List[CandidatePlace]:
        seen: Set[Tuple[str, str]] = set()
        results: List[CandidatePlace] = []
        collected_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        for search_query in queries:
            if len(results) >= _MIN_REQUIRED:
                break

            try:
                raw_items = self._client.search_places(search_query.query, _DISPLAY_PER_QUERY)
            except Exception as e:
                _logger.error("[Collector] search raised unexpectedly: query=%r error=%r", search_query.query, str(e))
                continue

            for raw in raw_items:
                address = raw.road_address or raw.address
                if not address:
                    continue

                name = _strip_html(raw.title)
                dedup_key = (name, address)
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                results.append(
                    CandidatePlace(
                        id=_place_id(name, address),
                        name=name,
                        category=raw.category,
                        road_address=raw.road_address,
                        address=raw.address,
                        mapx=raw.mapx,
                        mapy=raw.mapy,
                        link=raw.link,
                        telephone=raw.telephone,
                        keyword=search_query.keyword_label,
                        collected_at=collected_at,
                        place_type=search_query.place_type,
                        activity_kind=search_query.activity_kind,
                    )
                )

                if len(results) >= _MIN_REQUIRED:
                    break

        return results
