import uuid
from typing import List, Optional

from app.domains.recommendation.domain.value_object.ordered_place import OrderedPlace
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.domain.value_object.scored_course import ScoredCourse
from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    GetRecommendationResponseDto,
    RecommendationCourseItemDto,
    RecommendationPlaceDto,
)


class RecommendationResponseMapper:
    def to_response_dto(
        self,
        best: Optional[ScoredCourse],
        optionals: List[ScoredCourse],
        shortage_reasons: List[str],
    ) -> GetRecommendationResponseDto:
        courses: List[RecommendationCourseItemDto] = []

        if best is not None:
            courses.append(self._to_course_item(best, "best"))

        for optional in optionals:
            courses.append(self._to_course_item(optional, "optional"))

        return GetRecommendationResponseDto(
            courses=courses,
            shortage_reasons=shortage_reasons,
        )

    def _to_course_item(self, scored: ScoredCourse, grade: str) -> RecommendationCourseItemDto:
        places = scored.ordered_result.places
        return RecommendationCourseItemDto(
            course_id=str(uuid.uuid4()),
            grade=grade,
            restaurant=self._to_place_dto(self._extract(places, PlaceType.RESTAURANT)),
            cafe=self._to_place_dto(self._extract(places, PlaceType.CAFE)),
            activity=self._to_place_dto(self._extract(places, PlaceType.ACTIVITY)),
        )

    def _extract(self, places: List[OrderedPlace], place_type: PlaceType) -> OrderedPlace:
        return next(p for p in places if p.place_type == place_type)

    def _to_place_dto(self, ordered: OrderedPlace) -> RecommendationPlaceDto:
        cp = ordered.place
        return RecommendationPlaceDto(
            id=cp.id,
            name=cp.name,
            category=cp.category,
            road_address=cp.road_address,
            address=cp.address,
            mapx=cp.mapx,
            mapy=cp.mapy,
            link=cp.link,
            telephone=cp.telephone,
            keyword=cp.keyword,
            collected_at=cp.collected_at,
        )
