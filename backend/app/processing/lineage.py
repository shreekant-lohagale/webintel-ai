
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.processing.cleaning import sha256_hash
from app.processing.schemas import WebDocument


class SourceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: str
    document_id: str
    source_url: str
    extraction_method: Literal[
        "scrapy", "playwright", "httpx"
    ]
    content_hash: str

    first_seen_at: datetime
    last_seen_at: datetime


class DocumentRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: str
    document_id: str
    content_hash: str

    title: str
    content: str

    observed_at: datetime


def make_observation(
    document: WebDocument,
) -> SourceObservation:
    """
    Identify one unique source/method/content observation.

    Reprocessing the same scraped record does not
    create another unique observation.
    """

    observation_id = sha256_hash(
        "\n".join([
            document.document_id,
            str(document.source_url),
            document.extraction_method,
            document.content_hash,
        ])
    )

    return SourceObservation(
        observation_id=observation_id,
        document_id=document.document_id,
        source_url=str(document.source_url),
        extraction_method=document.extraction_method,
        content_hash=document.content_hash,
        first_seen_at=document.scraped_at,
        last_seen_at=document.scraped_at,
    )


def make_revision(
    document: WebDocument,
) -> DocumentRevision:
    """
    Identify a document version by logical ID
    and content hash.
    """

    revision_id = sha256_hash(
        document.document_id
        + "\n"
        + document.content_hash
    )

    return DocumentRevision(
        revision_id=revision_id,
        document_id=document.document_id,
        content_hash=document.content_hash,
        title=document.title,
        content=document.content,
        observed_at=document.scraped_at,
    )


def merge_observation(
    existing: SourceObservation,
    incoming: SourceObservation,
) -> SourceObservation:
    """Preserve the earliest and latest observations."""

    if existing.observation_id != incoming.observation_id:
        raise ValueError("Cannot merge different observations")

    return existing.model_copy(
        update={
            "first_seen_at": min(
                existing.first_seen_at,
                incoming.first_seen_at,
            ),
            "last_seen_at": max(
                existing.last_seen_at,
                incoming.last_seen_at,
            ),
        }
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
