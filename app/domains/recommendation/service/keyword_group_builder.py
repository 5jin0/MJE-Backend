from typing import Dict, List

from app.domains.recommendation.domain.value_object.activity_type import ActivityKind
from app.domains.recommendation.service.datalab_client_interface import DataLabKeywordGroup

_ACTIVITY_KEYWORD_TEMPLATES: Dict[str, List[str]] = {
    ActivityKind.EXHIBITION.value:  ["{area} 전시", "{area} 미술관", "{area} 갤러리"],
    ActivityKind.WALK.value:        ["{area} 산책", "{area} 공원", "{area} 거리"],
    ActivityKind.SHOPPING.value:    ["{area} 쇼핑", "{area} 소품샵", "{area} 편집샵"],
    ActivityKind.POPUP.value:       ["{area} 팝업스토어", "{area} 팝업"],
    ActivityKind.WORKSHOP.value:    ["{area} 공방", "{area} 클래스", "{area} 체험"],
    ActivityKind.INDOOR_PLAY.value: ["{area} 보드게임", "{area} 방탈출", "{area} 오락실"],
    ActivityKind.MOVIE.value:       ["{area} 영화관", "{area} 영화"],
    ActivityKind.KARAOKE.value:     ["{area} 노래방"],
    ActivityKind.BAR.value:         ["{area} 술집", "{area} 와인바", "{area} 칵테일바"],
    ActivityKind.NIGHT_VIEW.value:  ["{area} 야경", "{area} 전망대"],
    ActivityKind.SPORTS.value:      ["{area} 볼링", "{area} 스포츠", "{area} 액티비티"],
    ActivityKind.LATE_NIGHT.value:  ["{area} 심야데이트", "{area} 밤 데이트"],
}


class KeywordGroupBuilder:
    def build_for_area(self, area: str) -> List[DataLabKeywordGroup]:
        groups: List[DataLabKeywordGroup] = [
            DataLabKeywordGroup(
                group_name="RESTAURANT",
                keywords=[f"{area} 맛집", f"{area} 레스토랑", f"{area} 식당"],
            ),
            DataLabKeywordGroup(
                group_name="CAFE",
                keywords=[f"{area} 카페", f"{area} 커피"],
            ),
        ]
        for category, templates in _ACTIVITY_KEYWORD_TEMPLATES.items():
            groups.append(DataLabKeywordGroup(
                group_name=category,
                keywords=[t.format(area=area) for t in templates],
            ))
        return groups
