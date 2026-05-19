from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.domains.courses.repository.mysql_course_repository import MysqlCourseRepository
from app.domains.recommendation.service.mapper.course_detail_mysql_mapper import (
    build_course_detail_from_entity,
)
from app.domains.recommendation.controller.api.request_form.get_recommendation_request_form import (
    GetRecommendationRequestForm,
)
from app.domains.recommendation.controller.api.response_form.frontend_course_detail_response_form import (
    FrontendCourseDetailResponseForm,
)
from app.domains.recommendation.controller.api.response_form.get_recommendation_response_form import (
    GetRecommendationResponseForm,
)
from app.domains.recommendation.repository.redis_recommendation_session_repository import (
    RedisRecommendationSessionRepository,
    get_recommendation_session_repository,
)
from app.domains.recommendation.repository.recommendation_session_repository_interface import (
    RecommendationSessionRepositoryInterface,
)
from app.domains.recommendation.service.usecase.get_recommendation_usecase import (
    GetRecommendationUseCase,
)
from app.infrastructure.api.geocoding.kakao_geocoding_client import KakaoGeocodingClient
from app.infrastructure.api.search.kakao_search_client import KakaoSearchClient
from app.infrastructure.cache.redis_candidate_cache import RedisCandidateCache
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.config.config import settings
from app.infrastructure.database.database import get_db

router = APIRouter(prefix="/courses", tags=["recommendation"])


async def _get_session_repository(
    repository: RedisRecommendationSessionRepository = Depends(get_recommendation_session_repository),
) -> RecommendationSessionRepositoryInterface:
    return repository


async def _get_recommendation_usecase(
    repository: RecommendationSessionRepositoryInterface = Depends(_get_session_repository),
    db: AsyncSession = Depends(get_db),
) -> GetRecommendationUseCase:
    search_client = KakaoSearchClient(rest_api_key=settings.KAKAO_MAP_REST_API_KEY)
    redis_client = await get_redis()
    candidate_cache = RedisCandidateCache(redis_client)
    geocoding_client = KakaoGeocodingClient(rest_api_key=settings.KAKAO_MAP_REST_API_KEY)
    return GetRecommendationUseCase(
        session_repository=repository,
        search_client=search_client,
        candidate_cache=candidate_cache,
        geocoding_client=geocoding_client,
        course_repository=MysqlCourseRepository(db),
    )


@router.post("/recommendations", response_model=GetRecommendationResponseForm)
async def get_recommendations(
    form: GetRecommendationRequestForm,
    usecase: GetRecommendationUseCase = Depends(_get_recommendation_usecase),
) -> GetRecommendationResponseForm:
    dto = form.to_request()
    result = await usecase.execute(dto)
    return GetRecommendationResponseForm.from_response(result)


@router.get("/recommendations/{course_id}", response_model=FrontendCourseDetailResponseForm)
async def get_course_detail(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> FrontendCourseDetailResponseForm:
    repo = MysqlCourseRepository(db)
    entity = await repo.find_by_id(course_id)
    if entity is None:
        raise NotFoundError(f"코스를 찾을 수 없습니다: {course_id}")
    others = await repo.find_by_session_id(entity.session_id) if entity.session_id else []
    result = build_course_detail_from_entity(course_id, entity, others)
    return FrontendCourseDetailResponseForm.from_dto(result)
