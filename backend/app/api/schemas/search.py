
from typing import Literal

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=1000,
    )

    mode: Literal[
        "semantic",
        "keyword",
        "hybrid",
    ] = "hybrid"

    limit: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    document_type: Literal[
        "article",
        "quote",
    ] | None = None

    source_domain: str | None = Field(
        default=None,
        max_length=253,
    )


class SourceCitation(BaseModel):
    document_id: str
    chunk_id: str
    source_url: str
    title: str


class SearchHit(BaseModel):
    rank: int
    chunk_id: str
    document_id: str
    title: str
    text: str
    source_url: str
    source_domain: str
    document_type: str
    chunk_index: int
    content_hash: str
    config_key: str

    semantic_score: float | None
    bm25_score: float | None
    hybrid_score: float | None

    citation: SourceCitation


class SearchResponse(BaseModel):
    query: str
    mode: str
    count: int
    results: list[SearchHit]
