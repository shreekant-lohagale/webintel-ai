
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WebDocument(BaseModel):
    """Common storage and retrieval document contract."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    schema_version: Literal["1.0"] = "1.0"

    document_id: str = Field(
        min_length=64,
        max_length=64,
    )

    document_type: Literal["quote", "article"]

    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)

    source_url: HttpUrl
    source_domain: str = Field(min_length=1)

    author: str | None = None
    tags: list[str] = Field(default_factory=list)

    published_at: datetime | None = None
    scraped_at: datetime

    extraction_method: Literal[
        "scrapy",
        "playwright",
        "httpx",
    ]

    content_hash: str = Field(
        min_length=64,
        max_length=64,
    )

    metadata: dict[str, Any] = Field(default_factory=dict)
