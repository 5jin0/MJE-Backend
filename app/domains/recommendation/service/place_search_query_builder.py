from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.domains.recommendation.domain.value_object.activity_type import ActivityKind
from app.domains.recommendation.domain.value_object.place_type import PlaceType

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
    ActivityKind.WALK.value: ["{area} 산책", "{area} 공원"],
    ActivityKind.SHOPPING.value: ["{area} 쇼핑", "{area} 편집샵"],
    ActivityKind.POPUP.value: ["{area} 팝업스토어"],
    ActivityKind.WORKSHOP.value: ["{area} 공방", "{area} 체험"],
    ActivityKind.INDOOR_PLAY.value: ["{area} 보드게임", "{area} 방탈출"],
    ActivityKind.MOVIE.value: ["{area} 영화관"],
    ActivityKind.KARAOKE.value: ["{area} 노래방"],
    ActivityKind.BAR.value: ["{area} 술집", "{area} 와인바"],
    ActivityKind.NIGHT_VIEW.value: ["{area} 야경"],
    ActivityKind.SPORTS.value: ["{area} 볼링", "{area} 스포츠"],
    ActivityKind.LATE_NIGHT.value: ["{area} 심야 데이트"],
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

    def build_activity_queries(self, area: str) -> List[PlaceSearchQuery]:
        queries: List[PlaceSearchQuery] = []
        for variant in self._area_variants(area):
            for kind_value, templates in _ACTIVITY_TEMPLATES.items():
                activity_kind = ActivityKind(kind_value)
                for tmpl in templates:
                    query = tmpl.format(area=variant)
                    queries.append(
                        PlaceSearchQuery(
                            query=query,
                            keyword_label=query,
                            place_type=PlaceType.ACTIVITY,
                            activity_kind=activity_kind,
                        )
                    )
        return queries

    def _area_variants(self, area: str) -> List[str]:
        area = area.strip()
        if area in _AREA_ALIASES:
            raw_variants = _AREA_ALIASES[area]
        else:
            # 프론트에서 variant 이름("성수동")으로 들어올 때 canonical key 역방향 조회
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
