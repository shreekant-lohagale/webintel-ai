
import json

import pytest
from pydantic import ValidationError

from app.processing.normalizer import (
    normalize_article,
    normalize_quote,
)
from app.processing.cli import process_files


def sample_quote(source_url="https://quotes.toscrape.com/"):
    return {
        "text": "  Knowledge   is power.  ",
        "author": "  Francis Bacon  ",
        "tags": ["Wisdom", "wisdom", "Learning"],
        "source_url": source_url,
        "scraped_at": "2026-10-12T18:00:00+00:00",
    }


def test_normalize_quote():
    doc = normalize_quote(sample_quote())

    assert doc.document_type == "quote"
    assert doc.content == "Knowledge is power."
    assert doc.author == "Francis Bacon"
    assert doc.tags == ["wisdom", "learning"]
    assert doc.source_domain == "quotes.toscrape.com"
    assert doc.published_at is None
    assert len(doc.document_id) == 64


def test_duplicate_quote_identity():
    static_doc = normalize_quote(
        sample_quote("https://quotes.toscrape.com/"),
        extraction_method="scrapy",
    )

    dynamic_doc = normalize_quote(
        sample_quote("https://quotes.toscrape.com/js/"),
        extraction_method="playwright",
    )

    assert static_doc.document_id == dynamic_doc.document_id
    assert static_doc.content_hash == dynamic_doc.content_hash


def test_missing_content_rejected():
    record = sample_quote()
    record["text"] = ""

    with pytest.raises(ValueError):
        normalize_quote(record)


def test_missing_author_rejected():
    record = sample_quote()
    record["author"] = None

    with pytest.raises(ValueError):
        normalize_quote(record)


def test_naive_timestamp_rejected():
    record = sample_quote()
    record["scraped_at"] = "2026-10-12T18:00:00"

    with pytest.raises(ValueError):
        normalize_quote(record)


def test_invalid_method_rejected():
    with pytest.raises(ValidationError):
        normalize_quote(
            sample_quote(),
            extraction_method="unknown",
        )


def test_article_html_normalization():
    article = {
        "title": "  AI   Market Update ",
        "content_html": (
            "<article><p>AI hiring grows.</p>"
            "<script>track()</script></article>"
        ),
        "source_url": "https://example.com/news/ai",
        "scraped_at": "2026-10-12T18:00:00+00:00",
        "tags": ["AI"],
    }

    doc = normalize_article(article)

    assert doc.document_type == "article"
    assert doc.title == "AI Market Update"
    assert doc.content == "AI hiring grows."
    assert doc.tags == ["ai"]


def test_batch_deduplication(tmp_path):
    static_path = tmp_path / "static.json"
    dynamic_path = tmp_path / "dynamic.json"
    output_path = tmp_path / "documents.jsonl"

    static_path.write_text(
        json.dumps([sample_quote()]),
        encoding="utf-8",
    )

    dynamic_path.write_text(
        json.dumps([
            sample_quote(
                "https://quotes.toscrape.com/js/"
            )
        ]),
        encoding="utf-8",
    )

    report = process_files(
        [
            (static_path, "scrapy"),
            (dynamic_path, "playwright"),
        ],
        output_path,
    )

    assert report["input_records"] == 2
    assert report["unique_documents"] == 1
    assert report["duplicate_records"] == 1
    assert report["invalid_records"] == 0

    lines = output_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1
    assert json.loads(lines[0])["content"] == (
        "Knowledge is power."
    )
