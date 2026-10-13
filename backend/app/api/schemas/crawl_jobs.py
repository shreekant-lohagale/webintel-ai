
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


JobStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
]


class CrawlJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_url: str = Field(
        default="http://127.0.0.1:8766/",
        min_length=1,
        max_length=2048,
    )

    browser: bool = False


class CrawlJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    start_url: str
    browser: bool
    status: JobStatus

    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    error: str | None = None
    result: dict[str, Any] | None = None


class CrawlJobListResponse(BaseModel):
    items: list[CrawlJob]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    skip: int = Field(ge=0)
