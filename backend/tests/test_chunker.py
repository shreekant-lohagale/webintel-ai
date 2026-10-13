
import pytest

from app.embeddings.chunker import (
    CHUNKER_VERSION,
    chunk_text,
    make_chunk_id,
    normalize_for_chunks,
)


def test_whitespace_normalization():
    assert normalize_for_chunks(
        "Hello \n  web \t intelligence"
    ) == "Hello web intelligence"


def test_empty_content():
    assert chunk_text("  \n ") == []


def test_short_document_produces_one_chunk():
    result = chunk_text(
        "AI pipelines retrieve evidence.",
        chunk_words=20,
        overlap_words=5,
    )

    assert len(result) == 1
    assert result[0].chunk_index == 0
    assert result[0].word_start == 0
    assert result[0].word_end == 4


def test_overlapping_chunks():
    text = " ".join(
        f"word{i}" for i in range(10)
    )

    chunks = chunk_text(
        text,
        chunk_words=5,
        overlap_words=2,
    )

    assert len(chunks) == 3

    assert chunks[0].text == (
        "word0 word1 word2 word3 word4"
    )

    assert chunks[1].text == (
        "word3 word4 word5 word6 word7"
    )

    assert chunks[2].text == (
        "word6 word7 word8 word9"
    )


def test_chunking_is_deterministic():
    text = " ".join(["web", "AI"] * 30)

    first = chunk_text(
        text,
        chunk_words=12,
        overlap_words=3,
    )

    second = chunk_text(
        text,
        chunk_words=12,
        overlap_words=3,
    )

    assert first == second


def test_chunk_id_is_stable():
    args = (
        "doc123",
        "content456",
        0,
        "chunk789",
        "config123",
    )

    assert make_chunk_id(*args) == (
        make_chunk_id(*args)
    )


def test_changed_content_changes_chunk_id():
    first = make_chunk_id(
        "doc1", "hash1", 0, "chunk1", "config1"
    )

    second = make_chunk_id(
        "doc1", "hash2", 0, "chunk1", "config1"
    )

    assert first != second


@pytest.mark.parametrize(
    "chunk_words,overlap",
    [
        (0, 0),
        (10, -1),
        (10, 10),
        (10, 11),
    ],
)
def test_invalid_chunk_settings(
    chunk_words,
    overlap,
):
    with pytest.raises(ValueError):
        chunk_text(
            "some content",
            chunk_words=chunk_words,
            overlap_words=overlap,
        )
