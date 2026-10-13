
import pytest

from app.processing.normalizer import normalize_article
from app.processing.similarity import (
    find_near_duplicates,
    jaccard_similarity,
    tokenize,
    word_shingles,
)


BASE_TEXT = (
    "Artificial intelligence systems help businesses "
    "organize customer requests and automate repetitive "
    "workflows while improving response quality and "
    "reducing operational delays across service teams "
    "that handle large volumes of daily support tickets "
    "from customers in many different regions."
)


def article(url: str, text: str):
    return normalize_article({
        "title": "AI Customer Support",
        "content": text,
        "source_url": url,
        "scraped_at": "2026-10-13T08:00:00+00:00",
    })


def test_tokenization():
    assert tokenize("AI, Python! TEST") == [
        "ai", "python", "test"
    ]


def test_shingles():
    assert word_shingles(
        "AI improves customer service", 3
    ) == {
        ("ai", "improves", "customer"),
        ("improves", "customer", "service"),
    }


def test_identical_content_similarity():
    assert jaccard_similarity(
        BASE_TEXT, BASE_TEXT
    ) == 1.0


def test_different_content_similarity():
    assert jaccard_similarity(
        "red green blue yellow",
        "cat dog bird fish",
    ) == 0.0


def test_near_duplicate_articles():
    first = article(
        "https://example.com/article-a",
        BASE_TEXT,
    )

    second = article(
        "https://example.org/article-b",
        BASE_TEXT + " Additional reporting details.",
    )

    matches = find_near_duplicates(
        [first, second],
        threshold=0.80,
    )

    assert len(matches) == 1
    assert matches[0]["similarity_score"] >= 0.80
    assert matches[0]["method"] == "word_jaccard_3"


def test_same_document_not_linked_to_itself():
    first = article(
        "https://example.com/article-a",
        BASE_TEXT,
    )

    matches = find_near_duplicates([first, first])

    assert matches == []


def test_short_content_is_ignored():
    first = article(
        "https://example.com/short-a",
        "Breaking AI news",
    )

    second = article(
        "https://example.org/short-b",
        "Breaking AI news",
    )

    assert find_near_duplicates(
        [first, second]
    ) == []


def test_invalid_threshold():
    with pytest.raises(ValueError):
        find_near_duplicates(
            [],
            threshold=1.5,
        )
