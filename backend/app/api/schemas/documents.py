
from pydantic import BaseModel, Field

from app.processing.lineage import (
    DocumentRevision,
    SourceObservation,
)
from app.processing.schemas import WebDocument


class DocumentListResponse(BaseModel):
    items: list[WebDocument]

    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool


class DocumentSourcesResponse(BaseModel):
    document_id: str
    total: int = Field(ge=0)
    items: list[SourceObservation]


class DocumentRevisionsResponse(BaseModel):
    document_id: str
    total: int = Field(ge=0)
    items: list[DocumentRevision]
