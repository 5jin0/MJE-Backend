from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.domains.courses.domain.entity.course_entity import CoursePlace
from app.domains.courses.repository.mysql_course_repository import MysqlCourseRepository
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
from app.domains.recommendation.service.dto.request.get_course_detail_request_dto import (
    GetCourseDetailRequestDto,
)
from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    CourseDetailPlaceDto,
    GetCourseDetailResponseDto,
)
from app.domains.recommendation.service.usecase.get_course_detail_usecase import GetCourseDetailUseCase
from app.infrastructure.api.map.kakao_map_client import KakaoMapClient
from app.infrastructure.config.config import settings
from app.infrastructure.database.database import get_db

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


def _build_dto_from_mysql(course_id: str, entity) -> GetCourseDetailResponseDto:
    places = [
        CourseDetailPlaceDto(
            order=p.order,
            place_type=p.place_type,
            name=p.name,
            category=p.category,
            road_address=p.road_address,
            address=p.address,
            latitude=_parse_coord(p.mapy),
            longitude=_parse_coord(p.mapx),
            link=p.link,
            telephone=p.telephone,
            activity_type=None,
            image_url=None,
            start_time=p.start_time,
            end_time=p.end_time,
            duration_minutes=p.duration_minutes,
            move_time_to_next_minutes=p.move_time_to_next_minutes,
            short_description="",
        )
        for p in sorted(entity.places, key=lambda x: x.order)
    ]
    return GetCourseDetailResponseDto(
        course_id=entity.course_id,
        grade=entity.grade,
        area=entity.area,
        start_time=entity.start_time,
        transport=entity.transport,
        title=entity.title,
        description=entity.description,
        estimated_duration_minutes=entity.estimated_duration_minutes,
        places=places,
        other_courses=[],
    )


def _parse_coord(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


async def _get_dto(
    course_id: str,
    usecase: GetCourseDetailUseCase,
    db: AsyncSession,
) -> GetCourseDetailResponseDto:
    try:
        dto = GetCourseDetailRequestDto(course_id=course_id)
        return await usecase.execute(dto)
    except (NotFoundError, Exception):
        entity = await MysqlCourseRepository(db).find_by_id(course_id)
        if entity is None:
            raise NotFoundError(f"코스를 찾을 수 없습니다: {course_id}")
        return _build_dto_from_mysql(course_id, entity)


@router.get("/courses/{course_id}", response_model=FrontendCourseDetailResponseForm)
async def get_course_detail_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
    db: AsyncSession = Depends(get_db),
) -> FrontendCourseDetailResponseForm:
    result = await _get_dto(course_id, usecase, db)
    return FrontendCourseDetailResponseForm.from_dto(result)


@router.get("/detail/{course_id}/other-courses", response_model=FrontendOtherCoursesListForm)
async def get_other_courses_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
    db: AsyncSession = Depends(get_db),
) -> FrontendOtherCoursesListForm:
    result = await _get_dto(course_id, usecase, db)
    return FrontendOtherCoursesListForm.from_dto(result)


@router.get("/detail/{course_id}/activities", response_model=FrontendActivitiesListForm)
async def get_course_activities_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
    db: AsyncSession = Depends(get_db),
) -> FrontendActivitiesListForm:
    result = await _get_dto(course_id, usecase, db)
    return FrontendActivitiesListForm.from_dto(result)


@router.get("/detail/{course_id}/cafes", response_model=FrontendCafesListForm)
async def get_course_cafes_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
    db: AsyncSession = Depends(get_db),
) -> FrontendCafesListForm:
    result = await _get_dto(course_id, usecase, db)
    return FrontendCafesListForm.from_dto(result)


@router.get("/detail/{course_id}/restaurants", response_model=FrontendRestaurantsListForm)
async def get_course_restaurants_frontend(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
    db: AsyncSession = Depends(get_db),
) -> FrontendRestaurantsListForm:
    result = await _get_dto(course_id, usecase, db)
    return FrontendRestaurantsListForm.from_dto(result)
