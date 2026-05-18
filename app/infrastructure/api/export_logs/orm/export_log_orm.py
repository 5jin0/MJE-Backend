from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.infrastructure.database.database import Base


class ExportLogOrm(Base):
    __tablename__ = "export_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(50), nullable=False)
    session_id = Column(String(255), nullable=False)
    timestamp = Column(String(50), nullable=False)
    page_path = Column(String(500), nullable=False)
    course_id = Column(String(255), nullable=True)
    course_title = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)
