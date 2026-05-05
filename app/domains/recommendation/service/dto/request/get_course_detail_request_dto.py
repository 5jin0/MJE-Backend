from dataclasses import dataclass


@dataclass
class GetCourseDetailRequestDto:
    course_id: str
