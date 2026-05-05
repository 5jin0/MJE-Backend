from pydantic import BaseModel


class ExportLogResponseForm(BaseModel):
    success: bool
