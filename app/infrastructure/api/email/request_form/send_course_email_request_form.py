from pydantic import BaseModel, EmailStr


class SendCourseEmailRequestForm(BaseModel):
    email: EmailStr
    course_id: str
