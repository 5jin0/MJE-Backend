import logging

from fastapi import APIRouter, BackgroundTasks, Depends

from app.common.exceptions import NotFoundError
from app.domains.recommendation.repository.in_memory_recommendation_session_repository import (
    InMemoryRecommendationSessionRepository,
    get_recommendation_session_repository,
)
from app.domains.recommendation.service.dto.request.get_course_detail_request_dto import (
    GetCourseDetailRequestDto,
)
from app.domains.recommendation.service.usecase.get_course_detail_usecase import GetCourseDetailUseCase
from app.infrastructure.api.email.email_client import send_email
from app.infrastructure.api.email.email_template import build_course_email
from app.infrastructure.api.email.request_form.send_course_email_request_form import (
    SendCourseEmailRequestForm,
)
from app.infrastructure.api.email.response_form.send_course_email_response_form import (
    SendCourseEmailResponseForm,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])


def _get_detail_usecase(
    repository: InMemoryRecommendationSessionRepository = Depends(get_recommendation_session_repository),
) -> GetCourseDetailUseCase:
    return GetCourseDetailUseCase(repository=repository)


def _send_email_task(to: str, course_id: str, usecase: GetCourseDetailUseCase) -> None:
    try:
        detail = usecase.execute(GetCourseDetailRequestDto(course_id=course_id))
        subject, html, text = build_course_email(detail)
        send_email(to=to, subject=subject, body_html=html, body_text=text)
    except Exception as e:
        logger.error("Background email task failed to=%s course_id=%s error=%s", to, course_id, e)


@router.post("/send-course", response_model=SendCourseEmailResponseForm, status_code=200)
def send_course_email(
    form: SendCourseEmailRequestForm,
    background_tasks: BackgroundTasks,
    usecase: GetCourseDetailUseCase = Depends(_get_detail_usecase),
) -> SendCourseEmailResponseForm:
    usecase.execute(GetCourseDetailRequestDto(course_id=form.course_id))

    background_tasks.add_task(_send_email_task, str(form.email), form.course_id, usecase)

    return SendCourseEmailResponseForm(
        success=True,
        message=f"{form.email}로 코스 정보를 전송했습니다.",
    )
