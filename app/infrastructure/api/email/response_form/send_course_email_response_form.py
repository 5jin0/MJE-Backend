from pydantic import BaseModel


class SendCourseEmailResponseForm(BaseModel):
    success: bool
    message: str
