
import json

from app.processing.cli import process_files, read_jsonl
from app.processing.lineage import (
    DocumentRevision,
    SourceObservation,
    make_observation,
    make_revision,
    merge_observation,
)
from app.processing.normalizer import (
    normalize_article,
    normalize_quote,
)
from app.processing.schemas import WebDocument


def quote(
    url="https://quotes.toscrape.com/",
    method="scrapy",
):
    return normalize_quote(
        {
            "text": "Knowledge is power.",
            "author": "Francis Bacon",
            "tags": ["wisdom"],
            "source_url": url,
            "scraped_at": "2026-10-13T08:00:00+00:00",
        },
        extraction_method=method,
    )


def article_record(
    content: str,
    timestamp: str,
):
    return {
        "title": "AI Technology Report",
        "content": content,
        "source_url": "https://example.com/news/ai",
        "scraped_at": timestamp,
        "tags": ["AI"],
    }


def test_same_quote_has_stable_identity():
    first = quote()

    second = quote(
        "https://quotes.toscrape.com/js/",
        "playwright",
    )

    assert first.document_id == second.document_id


def test_different_sources_have_different_observations():
    first = make_observation(quote())

    second = make_observation(
        quote(
            "https://quotes.toscrape.com/js/",
            "playwright",
        )
    )

    assert first.document_id == second.document_id
    assert first.observation_id != second.observation_id


def test_reprocessing_observation_is_idempotent():
    first = make_observation(quote())
    second = make_observation(quote())

    assert first.observation_id == second.observation_id


def test_observation_merges_timestamps():
    first = make_observation(quote())

    newer = quote().model_copy(
        update={
            "scraped_at": first.last_seen_at.replace(
                year=2027
            )
        }
    )

    second = make_observation(newer)

    merged = merge_observation(first, second)

    assert merged.first_seen_at == first.first_seen_at
    assert merged.last_seen_at == second.last_seen_at


def test_article_revision_identity():
    first = normalize_article(
        article_record(
            "Original article content.",
            "2026-10-13T08:00:00+00:00",
        )
    )

    second = normalize_article(
        article_record(
            "Updated article content.",
            "2026-10-13T09:00:00+00:00",
        )
    )

    assert first.document_id == second.document_id
    assert first.content_hash != second.content_hash

    assert (
        make_revision(first).revision_id
        != make_revision(second).revision_id
    )


def test_batch_preserves_provenance(tmp_path):
    static_file = tmp_path / "static.json"
    dynamic_file = tmp_path / "dynamic.json"
    output_file = tmp_path / "documents.jsonl"

    first = {
        "text": "Knowledge is power.",
        "author": "Francis Bacon",
        "tags": ["wisdom"],
        "source_url": "https://quotes.toscrape.com/",
        "scraped_at": "2026-10-13T08:00:00+00:00",
    }

    second = {
        **first,
        "source_url": "https://quotes.toscrape.com/js/",
    }

    static_file.write_text(
        json.dumps([first]), encoding="utf-8"
    )

    dynamic_file.write_text(
        json.dumps([second]), encoding="utf-8"
    )

    inputs = [
        (static_file, "scrapy"),
        (dynamic_file, "playwright"),
    ]

    report = process_files(inputs, output_file)

    assert report["input_records"] == 2
    assert report["unique_documents"] == 1
    assert report["duplicate_records"] == 1
    assert report["source_observations"] == 2
    assert report["document_revisions"] == 1

    # Re-running the same input must not add new records.
    second_report = process_files(inputs, output_file)

    assert second_report["unique_documents"] == 1
    assert second_report["source_observations"] == 2
    assert second_report["document_revisions"] == 1


def test_article_updates_create_revisions(tmp_path):
    input_file = tmp_path / "articles.json"
    output_file = tmp_path / "documents.jsonl"

    input_file.write_text(
        json.dumps([
            article_record(
                "Original article content.",
                "2026-10-13T08:00:00+00:00",
            )
        ]),
        encoding="utf-8",
    )

    first_report = process_files(
        [(input_file, "scrapy", "article")],
        output_file,
    )

    assert first_report["unique_documents"] == 1
    assert first_report["document_revisions"] == 1

    input_file.write_text(
        json.dumps([
            article_record(
                "Updated article content.",
                "2026-10-13T09:00:00+00:00",
            )
        ]),
        encoding="utf-8",
    )

    second_report = process_files(
        [(input_file, "scrapy", "article")],
        output_file,
    )

    assert second_report["unique_documents"] == 1
    assert second_report["document_revisions"] == 2

    docs = read_jsonl(output_file, WebDocument)

    revisions = read_jsonl(
        tmp_path / "revisions.jsonl",
        DocumentRevision,
    )

    observations = read_jsonl(
        tmp_path / "provenance.jsonl",
        SourceObservation,
    )

    document = next(iter(docs.values()))

    assert document.content == "Updated article content."
    assert len(revisions) == 2
    assert len(observations) == 2
