from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UploadOut(BaseModel):
    document_id: str
    status: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(validation_alias="_id")
    filename: str
    upload_date: datetime
    page_count: int | None = 0
    status: str
    error: str | None = None
    summary: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, value: object) -> str:
        return str(value)


class ChatRequest(BaseModel):
    question: str
