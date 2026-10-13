
from datetime import datetime, timezone
from urllib.parse import urlsplit

from app.processing.cleaning import (
    canonicalize_url,
    clean_html,
    clean_text,
    normalize_tags,
    sha256_hash,
)
from app.processing.schemas import WebDocument


def parse_timestamp(value, field_name: str) -> datetime:
    """Convert timestamps to timezone-aware UTC datetimes."""

    if isinstance(value, str):
        value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    if not isinstance(value, datetime):
        raise ValueError(
            f"{field_name} must be a valid datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def normalize_quote(
    record: dict,
    extraction_method: str = "scrapy",
) -> WebDocument:
    """Convert a Phase 1 quote into a WebDocument."""

    content = clean_text(record.get("text"))
    author = clean_text(record.get("author"))

    if not content:
        raise ValueError("Quote content is missing")

    if not author:
        raise ValueError("Quote author is missing")

    source_url = canonicalize_url(
        record["source_url"]
    )

    source_domain = urlsplit(
        source_url
    ).hostname

    scraped_at = parse_timestamp(
        record.get("scraped_at"),
        "scraped_at",
    )

    # Hash of normalized quote text.
    content_hash = sha256_hash(content)

    # IMPORTANT:
    # Do not include source_url.
    # The same quote can appear on multiple listing pages.
    document_id = sha256_hash(
        "quote\n"
        + content
        + "\n"
        + author.casefold()
    )

    title = clean_text(content[:120])

    return WebDocument(
        document_id=document_id,
        document_type="quote",
        title=title,
        content=content,
        source_url=source_url,
        source_domain=source_domain,
        author=author,
        tags=normalize_tags(record.get("tags")),
        published_at=None,
        scraped_at=scraped_at,
        extraction_method=extraction_method,
        content_hash=content_hash,
        metadata={
            "original_source": "quotes_to_scrape",
            "record_kind": "quote",
        },
    )


def normalize_article(
    record: dict,
    extraction_method: str = "scrapy",
) -> WebDocument:
    """Normalize an extracted article into a WebDocument."""

    title = clean_text(record.get("title"))

    content = (
        clean_html(record["content_html"])
        if record.get("content_html")
        else clean_text(record.get("content"))
    )

    if not title:
        raise ValueError("Article title is missing")

    if not content:
        raise ValueError("Article content is missing")

    source_url = canonicalize_url(
        record["source_url"]
    )

    source_domain = urlsplit(
        source_url
    ).hostname

    author = clean_text(
        record.get("author")
    ) or None

    scraped_at = parse_timestamp(
        record.get(
            "scraped_at",
            datetime.now(timezone.utc),
        ),
        "scraped_at",
    )

    published_at = record.get("published_at")

    if published_at is not None:
        published_at = parse_timestamp(
            published_at,
            "published_at",
        )

    content_hash = sha256_hash(content)

    # Article identity is based on its canonical URL.
    # If the article changes, its document_id stays stable,
    # while content_hash changes.
    document_id = sha256_hash(
        "article\n" + source_url
    )

    return WebDocument(
        document_id=document_id,
        document_type="article",
        title=title,
        content=content,
        source_url=source_url,
        source_domain=source_domain,
        author=author,
        tags=normalize_tags(record.get("tags")),
        published_at=published_at,
        scraped_at=scraped_at,
        extraction_method=extraction_method,
        content_hash=content_hash,
        metadata={},
    )
