from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class ExportLogEventType(str, Enum):
    COURSE_SHARE = "course_share"
    COPY_LINK = "copy_link"
    SHARE_CLOSE = "share_close"

    @classmethod
    def allowed_values(cls) -> list[str]:
        return [e.value for e in cls]


class ExportLogRequestForm(BaseModel):
    event_name: str
    session_id: str
    timestamp: str
    page_path: str
    course_id: Optional[str] = None
    course_title: Optional[str] = None

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        allowed = ExportLogEventType.allowed_values()
        if v not in allowed:
            raise ValueError(f"event_name must be one of {allowed}")
        return v
