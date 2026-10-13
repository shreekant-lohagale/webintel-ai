
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=2, max_length=16)
    quote: str = Field(min_length=1, max_length=1000)


class GeneratedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=1000)
    evidence: list[EvidenceReference] = Field(
        min_length=1,
        max_length=3,
    )


class GeneratedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    abstain: bool
    claims: list[GeneratedClaim] = Field(
        default_factory=list,
        max_length=8,
    )


class AnswerCitation(BaseModel):
    evidence_id: str
    document_id: str
    chunk_id: str
    title: str
    source_url: str
    quote: str


class AnswerClaim(BaseModel):
    text: str
    citations: list[AnswerCitation]


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=1,
        max_length=1000,
    )
    mode: Literal["hybrid", "semantic", "keyword"] = (
        "hybrid"
    )
    top_k: int = Field(default=4, ge=1, le=8)
    document_type: Literal[
        "article",
        "quote",
    ] | None = None
    source_domain: str | None = Field(
        default=None,
        max_length=253,
    )


class AskResponse(BaseModel):
    question: str
    status: Literal["answered", "abstained"]
    answer: str
    claims: list[AnswerClaim]
    citations: list[AnswerCitation]
    retrieved_chunks: int
    model: str | None
    abstention_reason: str | None = None
