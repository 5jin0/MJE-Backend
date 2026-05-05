import uuid
from datetime import datetime

from app.domains.courses.domain.entity.course_entity import CourseEntity, CoursePlace
from app.domains.courses.domain.value_object.recommendation_place import RecommendationPlace
from app.domains.courses.repository.course_repository_interface import CourseRepositoryInterface
from app.domains.courses.service.dto.request.create_recommendation_request_dto import (
    CreateRecommendationRequestDto,
)
from app.domains.courses.service.dto.response.create_recommendation_response_dto import (
    CourseRecommendationItemDto,
    CreateRecommendationResponseDto,
    RecommendationPlaceDto,
)

_MOCK_TEMPLATES = [
    {
        "grade": "best",
        "title_suffix": "추천 코스",
        "restaurant": {"name": "한우 명가", "category": "음식점 > 한식 > 소고기,돼지고기", "keyword": "한우 맛집 데이트"},
        "cafe": {"name": "루프탑 카페", "category": "카페 > 커피전문점", "keyword": "루프탑 데이트 카페"},
        "activity": {"name": "VR 체험관", "category": "레저 > 오락 > VR체험", "keyword": "커플 VR 체험"},
    },
    {
        "grade": "optional",
        "title_suffix": "대안 코스 1",
        "restaurant": {"name": "스시 오마카세", "category": "음식점 > 일식 > 초밥,롤", "keyword": "오마카세 데이트"},
        "cafe": {"name": "브런치 카페", "category": "카페 > 브런치", "keyword": "분위기 좋은 카페"},
        "activity": {"name": "볼링장", "category": "레저 > 스포츠 > 볼링장", "keyword": "커플 볼링"},
    },
    {
        "grade": "optional",
        "title_suffix": "대안 코스 2",
        "restaurant": {"name": "이탈리안 레스토랑", "category": "음식점 > 양식 > 이탈리안", "keyword": "파스타 데이트"},
        "cafe": {"name": "디저트 카페", "category": "카페 > 디저트", "keyword": "케이크 카페"},
        "activity": {"name": "방탈출 카페", "category": "레저 > 오락 > 방탈출카페", "keyword": "커플 방탈출"},
    },
]

_TRANSPORT_LABELS = {"walk": "도보", "public_transit": "대중교통", "car": "자동차"}


class CreateCourseRecommendationsUseCase:
    def __init__(self, repository: CourseRepositoryInterface) -> None:
        self._repository = repository

    def execute(self, dto: CreateRecommendationRequestDto) -> CreateRecommendationResponseDto:
        collected_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        transport_label = _TRANSPORT_LABELS.get(dto.transport, dto.transport)
        courses = []

        for idx, template in enumerate(_MOCK_TEMPLATES):
            course_id = str(uuid.uuid4())
            base_id = (idx + 1) * 100

            restaurant = self._build_place(base_id + 1, dto.area, template["restaurant"], collected_at)
            cafe = self._build_place(base_id + 2, dto.area, template["cafe"], collected_at)
            activity = self._build_place(base_id + 3, dto.area, template["activity"], collected_at)

            places = [
                self._to_course_place(restaurant, "restaurant", 1, dto.start_time, 90, 15),
                self._to_course_place(cafe, "cafe", 2, self._add_minutes(dto.start_time, 105), 60, 10),
                self._to_course_place(activity, "activity", 3, self._add_minutes(dto.start_time, 175), 60, 0),
            ]

            entity = CourseEntity(
                course_id=course_id,
                grade=template["grade"],
                area=dto.area,
                start_time=dto.start_time,
                transport=dto.transport,
                title=f"{dto.area} {template['title_suffix']}",
                description=(
                    f"{dto.area}에서 즐기는 특별한 하루. "
                    f"{transport_label}으로 이동하며 맛집, 카페, 액티비티를 즐겨보세요."
                ),
                estimated_duration_minutes=235,
                restaurant=restaurant,
                cafe=cafe,
                activity=activity,
                places=places,
            )

            self._repository.save(entity)

            courses.append(
                CourseRecommendationItemDto(
                    course_id=course_id,
                    grade=template["grade"],
                    restaurant=self._to_place_dto(restaurant),
                    cafe=self._to_place_dto(cafe),
                    activity=self._to_place_dto(activity),
                )
            )

        return CreateRecommendationResponseDto(courses=courses, shortage_reasons=[])

    def _build_place(
        self, place_id: int, area: str, template: dict, collected_at: str
    ) -> RecommendationPlace:
        return RecommendationPlace(
            id=place_id,
            name=f"{area} {template['name']}",
            category=template["category"],
            road_address=f"서울 {area} 테헤란로 {place_id}길 {place_id}",
            address=f"서울 {area}",
            mapx="127.0276",
            mapy="37.4979",
            link="",
            telephone="02-1234-5678",
            keyword=template["keyword"],
            collected_at=collected_at,
        )

    def _to_place_dto(self, place: RecommendationPlace) -> RecommendationPlaceDto:
        return RecommendationPlaceDto(
            id=place.id,
            name=place.name,
            category=place.category,
            road_address=place.road_address,
            address=place.address,
            mapx=place.mapx,
            mapy=place.mapy,
            link=place.link,
            telephone=place.telephone,
            keyword=place.keyword,
            collected_at=place.collected_at,
        )

    def _to_course_place(
        self,
        place: RecommendationPlace,
        place_type: str,
        order: int,
        start_time: str,
        duration: int,
        move_time: int,
    ) -> CoursePlace:
        return CoursePlace(
            order=order,
            place_type=place_type,
            id=place.id,
            name=place.name,
            category=place.category,
            road_address=place.road_address,
            address=place.address,
            mapx=place.mapx,
            mapy=place.mapy,
            link=place.link,
            telephone=place.telephone,
            keyword=place.keyword,
            collected_at=place.collected_at,
            start_time=start_time,
            end_time=self._add_minutes(start_time, duration),
            duration_minutes=duration,
            move_time_to_next_minutes=move_time,
        )

    @staticmethod
    def _add_minutes(time_str: str, minutes: int) -> str:
        h, m = map(int, time_str.split(":"))
        total = h * 60 + m + minutes
        return f"{total // 60 % 24:02d}:{total % 60:02d}"
