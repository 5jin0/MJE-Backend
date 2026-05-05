from fastapi import APIRouter, Depends

from app.domains.recommendation.controller.api.request_form.get_recommendation_request_form import (
    GetRecommendationRequestForm,
)
from app.domains.recommendation.controller.api.response_form.get_course_detail_response_form import (
    GetCourseDetailResponseForm,
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
from app.domains.recommendation.service.dto.request.get_course_detail_request_dto import (
    GetCourseDetailRequestDto,
)
from app.domains.recommendation.service.usecase.get_course_detail_usecase import GetCourseDetailUseCase
from app.domains.recommendation.service.usecase.get_recommendation_usecase import (
    GetRecommendationUseCase,
)
from app.infrastructure.api.image_search.naver_image_search_client import NaverImageSearchClient
from app.infrastructure.api.search.naver_search_client import NaverSearchClient
from app.infrastructure.cache.redis_candidate_cache import RedisCandidateCache
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.config.config import settings

router = APIRouter(prefix="/courses", tags=["recommendation"])


async def _get_session_repository(
    repository: RedisRecommendationSessionRepository = Depends(get_recommendation_session_repository),
) -> RecommendationSessionRepositoryInterface:
    return repository


async def _get_recommendation_usecase(
    repository: RecommendationSessionRepositoryInterface = Depends(_get_session_repository),
) -> GetRecommendationUseCase:
    search_client = NaverSearchClient(
        client_id=settings.NAVER_SEARCH_CLIENT_ID,
        client_secret=settings.NAVER_SEARCH_CLIENT_SECRET,
    )
    image_search_client = NaverImageSearchClient(
        client_id=settings.NAVER_SEARCH_CLIENT_ID,
        client_secret=settings.NAVER_SEARCH_CLIENT_SECRET,
    )
    redis_client = await get_redis()
    candidate_cache = RedisCandidateCache(redis_client)
    return GetRecommendationUseCase(
        session_repository=repository,
        search_client=search_client,
        image_search_client=image_search_client,
        candidate_cache=candidate_cache,
    )


def _get_course_detail_usecase(
    repository: RecommendationSessionRepositoryInterface = Depends(_get_session_repository),
) -> GetCourseDetailUseCase:
    return GetCourseDetailUseCase(repository=repository)


@router.post("/recommendations", response_model=GetRecommendationResponseForm)
async def get_recommendations(
    form: GetRecommendationRequestForm,
    usecase: GetRecommendationUseCase = Depends(_get_recommendation_usecase),
) -> GetRecommendationResponseForm:
    dto = form.to_request()
    result = await usecase.execute(dto)
    return GetRecommendationResponseForm.from_response(result)


@router.get("/recommendations/{course_id}", response_model=GetCourseDetailResponseForm)
async def get_course_detail(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
) -> GetCourseDetailResponseForm:
    dto = GetCourseDetailRequestDto(course_id=course_id)
    result = await usecase.execute(dto)
    return GetCourseDetailResponseForm.from_response(result)
