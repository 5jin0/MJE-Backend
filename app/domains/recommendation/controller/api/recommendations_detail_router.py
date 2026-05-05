from fastapi import APIRouter, Depends

from app.domains.recommendation.controller.api.response_form.frontend_course_detail_response_form import (
    FrontendCourseDetailResponseForm,
    FrontendOtherCoursesListForm,
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

router = APIRouter(prefix="/recommendations", tags=["recommendation"])


async def _get_session_repository(
    repository: RedisRecommendationSessionRepository = Depends(get_recommendation_session_repository),
) -> RecommendationSessionRepositoryInterface:
    return repository


def _get_course_detail_usecase(
    repository: RecommendationSessionRepositoryInterface = Depends(_get_session_repository),
) -> GetCourseDetailUseCase:
    return GetCourseDetailUseCase(repository=repository)


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
