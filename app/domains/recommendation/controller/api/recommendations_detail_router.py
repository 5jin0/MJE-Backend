from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.domains.courses.repository.mysql_course_repository import MysqlCourseRepository
from app.domains.recommendation.controller.api.response_form.frontend_course_detail_response_form import (
    FrontendActivitiesListForm,
    FrontendCafesListForm,
    FrontendCourseDetailResponseForm,
    FrontendOtherCoursesListForm,
    FrontendRestaurantsListForm,
)
from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    GetCourseDetailResponseDto,
)
from app.domains.recommendation.service.mapper.course_detail_mysql_mapper import (
    build_course_detail_from_entity,
)
from app.infrastructure.database.database import get_db

router = APIRouter(prefix="/recommendations", tags=["recommendation"])


async def _get_dto(course_id: str, db: AsyncSession) -> GetCourseDetailResponseDto:
    repo = MysqlCourseRepository(db)
    entity = await repo.find_by_id(course_id)
    if entity is None:
        raise NotFoundError(f"코스를 찾을 수 없습니다: {course_id}")
    others = await repo.find_by_session_id(entity.session_id) if entity.session_id else []
    return build_course_detail_from_entity(course_id, entity, others)


@router.get("/courses/{course_id}", response_model=FrontendCourseDetailResponseForm)
async def get_course_detail_frontend(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> FrontendCourseDetailResponseForm:
    result = await _get_dto(course_id, db)
    return FrontendCourseDetailResponseForm.from_dto(result)


@router.get("/detail/{course_id}/other-courses", response_model=FrontendOtherCoursesListForm)
async def get_other_courses_frontend(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> FrontendOtherCoursesListForm:
    result = await _get_dto(course_id, db)
    return FrontendOtherCoursesListForm.from_dto(result)


@router.get("/detail/{course_id}/activities", response_model=FrontendActivitiesListForm)
async def get_course_activities_frontend(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> FrontendActivitiesListForm:
    result = await _get_dto(course_id, db)
    return FrontendActivitiesListForm.from_dto(result)


@router.get("/detail/{course_id}/cafes", response_model=FrontendCafesListForm)
async def get_course_cafes_frontend(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> FrontendCafesListForm:
    result = await _get_dto(course_id, db)
    return FrontendCafesListForm.from_dto(result)


@router.get("/detail/{course_id}/restaurants", response_model=FrontendRestaurantsListForm)
async def get_course_restaurants_frontend(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> FrontendRestaurantsListForm:
    result = await _get_dto(course_id, db)
    return FrontendRestaurantsListForm.from_dto(result)
