from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.courses.controller.api.request_form.course_event_request_form import (
    CourseEventRequestForm,
)
from app.domains.courses.controller.api.request_form.create_recommendation_request_form import (
    CreateRecommendationRequestForm,
)
from app.domains.courses.controller.api.response_form.course_event_response_form import (
    CourseEventResponseForm,
)
from app.domains.courses.controller.api.response_form.create_recommendation_response_form import (
    CreateRecommendationResponseForm,
)
from app.domains.courses.controller.api.response_form.get_course_detail_response_form import (
    GetCourseDetailResponseForm,
)
from app.domains.courses.repository.course_repository_interface import CourseRepositoryInterface
from app.domains.courses.repository.in_memory_course_repository import get_course_repository
from app.domains.courses.repository.mysql_courses_event_repository import MysqlCoursesEventRepository
from app.domains.courses.service.usecase.create_course_recommendations_usecase import (
    CreateCourseRecommendationsUseCase,
)
from app.domains.courses.service.usecase.get_course_detail_usecase import GetCourseDetailUseCase
from app.domains.courses.service.usecase.record_courses_event_usecase import RecordCoursesEventUseCase
from app.infrastructure.database.database import get_db

router = APIRouter(prefix="/courses", tags=["courses"])


def _get_create_recommendations_usecase(
    repository: CourseRepositoryInterface = Depends(get_course_repository),
) -> CreateCourseRecommendationsUseCase:
    return CreateCourseRecommendationsUseCase(repository)


def _get_course_detail_usecase(
    repository: CourseRepositoryInterface = Depends(get_course_repository),
) -> GetCourseDetailUseCase:
    return GetCourseDetailUseCase(repository)


@router.post("/events", response_model=CourseEventResponseForm, status_code=200)
async def record_course_event(
    form: CourseEventRequestForm,
    db: AsyncSession = Depends(get_db),
) -> CourseEventResponseForm:
    repository = MysqlCoursesEventRepository(db)
    usecase = RecordCoursesEventUseCase(repository)
    dto = await usecase.execute(form.to_request())
    return CourseEventResponseForm.from_response(dto)


@router.post("/recommendations", response_model=CreateRecommendationResponseForm)
def create_recommendations(
    form: CreateRecommendationRequestForm,
    usecase: CreateCourseRecommendationsUseCase = Depends(_get_create_recommendations_usecase),
) -> CreateRecommendationResponseForm:
    dto = form.to_request()
    result = usecase.execute(dto)
    return CreateRecommendationResponseForm.from_response(result)


@router.get("/{course_id}", response_model=GetCourseDetailResponseForm)
def get_course_detail(
    course_id: str,
    usecase: GetCourseDetailUseCase = Depends(_get_course_detail_usecase),
) -> GetCourseDetailResponseForm:
    result = usecase.execute(course_id)
    return GetCourseDetailResponseForm.from_response(result)
