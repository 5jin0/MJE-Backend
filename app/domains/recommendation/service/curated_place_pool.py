from dataclasses import dataclass
from typing import Dict, List, Optional

from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.service.place_search_query_builder import ActivityKind

CURATED_SCORE = 0.6


@dataclass(frozen=True)
class CuratedPlaceConfig:
    search_query: str
    place_type: PlaceType
    activity_kind: Optional[ActivityKind] = None


_SEONGSU_PLACES: List[CuratedPlaceConfig] = [
    # 레스토랑
    CuratedPlaceConfig("죠죠 성수", PlaceType.RESTAURANT),
    CuratedPlaceConfig("HDD피자 성수", PlaceType.RESTAURANT),
    CuratedPlaceConfig("진작다이닝 성수", PlaceType.RESTAURANT),
    CuratedPlaceConfig("동구식당 성수", PlaceType.RESTAURANT),
    CuratedPlaceConfig("투파인드피터 서울성수점", PlaceType.RESTAURANT),
    CuratedPlaceConfig("바오 서울 성수", PlaceType.RESTAURANT),
    CuratedPlaceConfig("고우 성수", PlaceType.RESTAURANT),
    # 카페
    CuratedPlaceConfig("사이드템포 성수", PlaceType.CAFE),
    CuratedPlaceConfig("언라인 성수", PlaceType.CAFE),
    CuratedPlaceConfig("따우전드 성수", PlaceType.CAFE),
    # Activity - 체험 (WORKSHOP)
    CuratedPlaceConfig("모나미 스토어 성수점", PlaceType.ACTIVITY, ActivityKind.WORKSHOP),
    CuratedPlaceConfig("포인트오브뷰 성수", PlaceType.ACTIVITY, ActivityKind.WORKSHOP),
    CuratedPlaceConfig("데이지크 성수", PlaceType.ACTIVITY, ActivityKind.WORKSHOP),
    CuratedPlaceConfig("탬버린즈 성수", PlaceType.ACTIVITY, ActivityKind.WORKSHOP),
    # Activity - 전시/문화 (EXHIBITION)
    CuratedPlaceConfig("LCDC Seoul", PlaceType.ACTIVITY, ActivityKind.EXHIBITION),
    CuratedPlaceConfig("성수연방", PlaceType.ACTIVITY, ActivityKind.EXHIBITION),
    # Activity - 칵테일바/와인바 (BAR, NIGHTLIFE)
    CuratedPlaceConfig("페어드 칵테일 성수", PlaceType.ACTIVITY, ActivityKind.BAR),
    CuratedPlaceConfig("리타르단도 성수", PlaceType.ACTIVITY, ActivityKind.BAR),
    CuratedPlaceConfig("포도젝트 성수", PlaceType.ACTIVITY, ActivityKind.BAR),
    CuratedPlaceConfig("기러기둥지 성수", PlaceType.ACTIVITY, ActivityKind.BAR),
]

_CURATED_BY_AREA: Dict[str, List[CuratedPlaceConfig]] = {
    "성수": _SEONGSU_PLACES,
    "성수동": _SEONGSU_PLACES,
    "성수역": _SEONGSU_PLACES,
}


def get_curated_configs(area: str) -> List[CuratedPlaceConfig]:
    return _CURATED_BY_AREA.get(area.strip(), [])
