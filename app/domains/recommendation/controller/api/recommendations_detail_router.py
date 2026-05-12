from fastapi import APIRouter, Depends

from app.domains.recommendation.controller.api.response_form.frontend_course_detail_response_form import (
    FrontendActivitiesListForm,
    FrontendCafesListForm,
    FrontendCourseDetailResponseForm,
    FrontendOtherCoursesListForm,
    FrontendRestaurantsListForm,
)
from app.domains.recommendation.repository.redis_recommendation_session_repository import (
    RedisRecommendationSessionRepository,
    get_recommendation_session_repository,
)
from app.domains.recommendation.repository.recommendation_session_repository_interface import (
    RecommendationSessionRepositoryInterface,
)
from app.infrastructure.api.map.kakao_map_client import KakaoMapClient
from app.infrastructure.config.config import settings
from app.domains.recommendation.service.dto.request.get_course_detail_request_dto import (
    GetCourseDetailRequestDto,
)
from app.domains.recommendation.service.usecase.get_course_detail_usecase import GetCourseDetailUseCase

router = APIRouter(prefix="/recommendations", tags=["recommendation"])


async def _get_session_repository(
    repository: RedisRecommendationSessionRepository = Depends(get_recommendation_session_repository),
) -> RecommendationSessionRepositoryInterface:
    return repository


def _get_course_detail_usecase(
    repository: RecommendationSessionRepositoryInterface = Depends(_get_session_repository),
) -> GetCourseDetailUseCase:
    map_client = KakaoMapClient(rest_api_key=settings.KAKAO_MAP_REST_API_KEY) if settings.KAKAO_MAP_REST_API_KEY else None
    return GetCourseDetailUseCase(repository=repository, map_client=map_client)


@router.get("/courses/{course_id}", response_model=FrontendCourseDetailResponseForm)
async def get_course_detail_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
) -> FrontendCourseDetailResponseForm:
    dto = GetCourseDetailRequestDto(course_id=course_id)
    result = await usecase.execute(dto)
    return FrontendCourseDetailResponseForm.from_dto(result)


@router.get("/detail/{course_id}/other-courses", response_model=FrontendOtherCoursesListForm)
async def get_other_courses_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
) -> FrontendOtherCoursesListForm:
    dto = GetCourseDetailRequestDto(course_id=course_id)
    result = await usecase.execute(dto)
    return FrontendOtherCoursesListForm.from_dto(result)


@router.get("/detail/{course_id}/activities", response_model=FrontendActivitiesListForm)
async def get_course_activities_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
) -> FrontendActivitiesListForm:
    dto = GetCourseDetailRequestDto(course_id=course_id)
    result = await usecase.execute(dto)
    return FrontendActivitiesListForm.from_dto(result)


@router.get("/detail/{course_id}/cafes", response_model=FrontendCafesListForm)
async def get_course_cafes_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
) -> FrontendCafesListForm:
    dto = GetCourseDetailRequestDto(course_id=course_id)
    result = await usecase.execute(dto)
    return FrontendCafesListForm.from_dto(result)


@router.get("/detail/{course_id}/restaurants", response_model=FrontendRestaurantsListForm)
async def get_course_restaurants_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
) -> FrontendRestaurantsListForm:
    dto = GetCourseDetailRequestDto(course_id=course_id)
    result = await usecase.execute(dto)
    return FrontendRestaurantsListForm.from_dto(result)
