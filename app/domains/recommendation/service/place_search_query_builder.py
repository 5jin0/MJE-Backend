from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from app.domains.recommendation.domain.value_object.activity_type import ActivityType
from app.domains.recommendation.domain.value_object.place_type import PlaceType


class ActivityKind(Enum):
    EXHIBITION = "exhibition"
    WALK = "walk"
    PARK = "park"
    SHOPPING = "shopping"
    POPUP = "popup"
    WORKSHOP = "workshop"
    INDOOR_PLAY = "indoor_play"
    MOVIE = "movie"
    KARAOKE = "karaoke"
    BAR = "bar"
    NIGHT_VIEW = "night_view"
    SPORTS = "sports"
    LATE_NIGHT = "late_night"
    BOOK_CAFE = "book_cafe"

    @property
    def activity_type(self) -> ActivityType:
        return _KIND_TO_TYPE[self]

    @property
    def is_daytime(self) -> bool:
        return self not in _NIGHTLIFE_KINDS

    @property
    def is_core(self) -> bool:
        return self.is_daytime

    @property
    def duration_minutes(self) -> int:
        return _KIND_DURATIONS.get(self, 120)


_NIGHTLIFE_KINDS = frozenset({
    ActivityKind.KARAOKE, ActivityKind.BAR, ActivityKind.NIGHT_VIEW, ActivityKind.LATE_NIGHT,
})

_KIND_TO_TYPE: Dict[ActivityKind, ActivityType] = {
    ActivityKind.EXHIBITION: ActivityType.EXHIBITION,
    ActivityKind.WALK: ActivityType.WALK,
    ActivityKind.PARK: ActivityType.PARK,
    ActivityKind.SHOPPING: ActivityType.SHOPPING,
    ActivityKind.POPUP: ActivityType.EXPERIENCE,
    ActivityKind.WORKSHOP: ActivityType.EXPERIENCE,
    ActivityKind.INDOOR_PLAY: ActivityType.EXPERIENCE,
    ActivityKind.MOVIE: ActivityType.MOVIE,
    ActivityKind.KARAOKE: ActivityType.NIGHTLIFE,
    ActivityKind.BAR: ActivityType.NIGHTLIFE,
    ActivityKind.NIGHT_VIEW: ActivityType.NIGHTLIFE,
    ActivityKind.SPORTS: ActivityType.EXPERIENCE,
    ActivityKind.LATE_NIGHT: ActivityType.NIGHTLIFE,
    ActivityKind.BOOK_CAFE: ActivityType.EXPERIENCE,
}

_KIND_DURATIONS: Dict[ActivityKind, int] = {
    ActivityKind.MOVIE: 130,
    ActivityKind.EXHIBITION: 90,
    ActivityKind.WORKSHOP: 90,
    ActivityKind.INDOOR_PLAY: 90,
    ActivityKind.BOOK_CAFE: 60,
    ActivityKind.KARAOKE: 90,
    ActivityKind.BAR: 90,
    ActivityKind.NIGHT_VIEW: 60,
    ActivityKind.LATE_NIGHT: 60,
    ActivityKind.SPORTS: 90,
}

_AREA_ALIASES: Dict[str, List[str]] = {
    "성수": ["성수", "성수동", "성수역"],
    "한남": ["한남", "한남동"],
    "홍대": ["홍대", "홍대입구", "홍대입구역"],
    "연남": ["연남", "연남동"],
    "망원": ["망원", "망원동"],
    "이태원": ["이태원", "이태원동"],
    "건대": ["건대", "건대입구", "건대입구역"],
    "잠실": ["잠실", "잠실역"],
    "혜화": ["혜화", "혜화역", "대학로"],
    "압구정": ["압구정", "압구정동", "압구정로데오"],
    "가로수길": ["가로수길", "신사 가로수길", "가로수"],
}

_RESTAURANT_TEMPLATES = [
    ("{area} 맛집", "맛집"),
    ("{area} 식당", "식당"),
    ("{area} 데이트 식당", "데이트 식당"),
    ("{area} 레스토랑", "레스토랑"),
    ("{area} 한식", "한식"),
]

_CAFE_TEMPLATES = [
    ("{area} 카페", "카페"),
    ("{area} 디저트 카페", "디저트 카페"),
    ("{area} 감성 카페", "감성 카페"),
]

_ACTIVITY_TEMPLATES: Dict[str, List[str]] = {
    ActivityKind.EXHIBITION.value: ["{area} 전시", "{area} 미술관"],
    ActivityKind.WALK.value: ["{area} 산책로", "{area} 데이트 산책"],
    ActivityKind.PARK.value: ["{area} 공원"],
    ActivityKind.SHOPPING.value: ["{area} 쇼핑", "{area} 편집샵"],
    ActivityKind.POPUP.value: ["{area} 팝업스토어"],
    ActivityKind.WORKSHOP.value: ["{area} 공방", "{area} 체험"],
    ActivityKind.INDOOR_PLAY.value: ["{area} 보드게임", "{area} 방탈출"],
    ActivityKind.MOVIE.value: ["{area} 영화관"],
    ActivityKind.KARAOKE.value: ["{area} 노래방"],
    ActivityKind.BAR.value: ["{area} 술집", "{area} 와인바"],
    ActivityKind.NIGHT_VIEW.value: ["{area} 야경", "{area} 야경카페", "{area} 루프탑"],
    ActivityKind.SPORTS.value: ["{area} 볼링", "{area} 클라이밍", "{area} 당구장"],
    ActivityKind.LATE_NIGHT.value: ["{area} 포장마차", "{area} 포차"],
    ActivityKind.BOOK_CAFE.value: ["{area} 북카페", "{area} 만화카페"],
}


@dataclass
class PlaceSearchQuery:
    query: str
    keyword_label: str
    place_type: PlaceType
    activity_kind: Optional[ActivityKind] = field(default=None)


class PlaceSearchQueryBuilder:
    def build_restaurant_queries(self, area: str) -> List[PlaceSearchQuery]:
        queries: List[PlaceSearchQuery] = []
        for variant in self._area_variants(area):
            for tmpl, label in _RESTAURANT_TEMPLATES:
                queries.append(
                    PlaceSearchQuery(
                        query=tmpl.format(area=variant),
                        keyword_label=label,
                        place_type=PlaceType.RESTAURANT,
                    )
                )
        return queries

    def build_cafe_queries(self, area: str) -> List[PlaceSearchQuery]:
        queries: List[PlaceSearchQuery] = []
        for variant in self._area_variants(area):
            for tmpl, label in _CAFE_TEMPLATES:
                queries.append(
                    PlaceSearchQuery(
                        query=tmpl.format(area=variant),
                        keyword_label=label,
                        place_type=PlaceType.CAFE,
                    )
                )
        return queries

    def build_activity_queries_for_kind(self, area: str, kind: ActivityKind) -> List[PlaceSearchQuery]:
        primary = self._area_variants(area)[0]
        return [
            PlaceSearchQuery(
                query=tmpl.format(area=primary),
                keyword_label=tmpl.format(area=primary),
                place_type=PlaceType.ACTIVITY,
                activity_kind=kind,
            )
            for tmpl in _ACTIVITY_TEMPLATES[kind.value]
        ]

    def _area_variants(self, area: str) -> List[str]:
        area = area.strip()
        if area in _AREA_ALIASES:
            raw_variants = _AREA_ALIASES[area]
        else:
            canonical = next(
                (key for key, vals in _AREA_ALIASES.items() if area in vals),
                None,
            )
            raw_variants = _AREA_ALIASES[canonical] if canonical else [area]

        deduped: List[str] = []
        for variant in raw_variants:
            if variant and variant not in deduped:
                deduped.append(variant)
        return deduped
