from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.api.export_logs.orm.export_log_orm import ExportLogOrm
from app.infrastructure.api.export_logs.request_form.export_log_request_form import ExportLogRequestForm
from app.infrastructure.api.export_logs.response_form.export_log_response_form import ExportLogResponseForm
from app.infrastructure.database.database import get_db

router = APIRouter(prefix="/api/v1/export-logs", tags=["export-logs"])


@router.post("", response_model=ExportLogResponseForm, status_code=200)
async def record_export_log(
    form: ExportLogRequestForm,
    db: AsyncSession = Depends(get_db),
) -> ExportLogResponseForm:
    log = ExportLogOrm(
        event_name=form.event_name,
        session_id=form.session_id,
        timestamp=form.timestamp,
        page_path=form.page_path,
    )
    db.add(log)
    await db.flush()
    return ExportLogResponseForm(success=True)
