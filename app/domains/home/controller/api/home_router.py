from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.home.controller.api.request_form.home_event_request_form import HomeEventRequestForm
from app.domains.home.controller.api.response_form.home_event_response_form import HomeEventResponseForm
from app.domains.home.repository.mysql_home_event_repository import MysqlHomeEventRepository
from app.domains.home.service.usecase.record_home_event_usecase import RecordHomeEventUseCase
from app.infrastructure.database.database import get_db

router = APIRouter(prefix="/home", tags=["home"])


@router.post("/events", response_model=HomeEventResponseForm, status_code=200)
async def record_home_event(
    form: HomeEventRequestForm,
    db: AsyncSession = Depends(get_db),
) -> HomeEventResponseForm:
    repository = MysqlHomeEventRepository(db)
    usecase = RecordHomeEventUseCase(repository)
    dto = await usecase.execute(form.to_request())
    return HomeEventResponseForm.from_response(dto)
