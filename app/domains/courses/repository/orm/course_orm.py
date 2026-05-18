from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.database.database import Base


class CourseOrm(Base):
    __tablename__ = "courses"

    course_id = Column(String(36), primary_key=True)
    grade = Column(String(50), nullable=False)
    area = Column(String(100), nullable=False)
    start_time = Column(String(10), nullable=False)
    transport = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)

    places = relationship("CoursePlaceOrm", back_populates="course", cascade="all, delete-orphan", lazy="selectin")


class CoursePlaceOrm(Base):
    __tablename__ = "course_places"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String(36), ForeignKey("courses.course_id"), nullable=False)
    place_order = Column(Integer, nullable=False)
    place_type = Column(String(50), nullable=False)
    place_id = Column(Integer, nullable=True)
    name = Column(String(500), nullable=False)
    category = Column(String(500), nullable=True)
    road_address = Column(String(1000), nullable=True)
    address = Column(String(1000), nullable=True)
    mapx = Column(String(50), nullable=True)
    mapy = Column(String(50), nullable=True)
    link = Column(String(2000), nullable=True)
    telephone = Column(String(100), nullable=True)
    keyword = Column(String(500), nullable=True)
    collected_at = Column(String(50), nullable=True)
    start_time = Column(String(10), nullable=True)
    end_time = Column(String(10), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    move_time_to_next_minutes = Column(Integer, nullable=True)

    course = relationship("CourseOrm", back_populates="places")
