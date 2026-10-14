
from datetime import datetime, timezone

import pytest

from app.intelligence.changes import compare_revisions


def revision(
    revision_id,
    content,
    content_hash,
    title="AI Report",
    document_id="doc-1",
):
    return {
        "revision_id": revision_id,
        "document_id": document_id,
        "title": title,
        "content": content,
        "content_hash": content_hash,
        "observed_at": datetime(
            2026, 10, 14, tzinfo=timezone.utc
        ),
    }


def test_added_words():
    old = revision(
        "rev1",
        "AI improves workflows.",
        "hash1",
    )
    new = revision(
        "rev2",
        "AI improves workflows with automation.",
        "hash2",
    )

    result = compare_revisions(old, new)

    assert result["content_changed"]
    assert result["added_words"] == 2
    assert result["removed_words"] == 0


def test_removed_words():
    old = revision(
        "rev1",
        "AI systems process data efficiently.",
        "hash1",
    )
    new = revision(
        "rev2",
        "AI systems process data",
        "hash2",
    )

    result = compare_revisions(old, new)

    assert result["removed_words"] == 1


def test_replaced_words():
    old = revision(
        "rev1",
        "The platform uses manual processing.",
        "hash1",
    )
    new = revision(
        "rev2",
        "The platform uses automated processing.",
        "hash2",
    )

    result = compare_revisions(old, new)

    assert result["added_words"] == 1
    assert result["removed_words"] == 1
    assert result["changes"][0]["kind"] == "replace"


def test_title_change():
    old = revision(
        "rev1", "Same content", "same"
    )
    new = revision(
        "rev2", "Same content", "same",
        title="Updated AI Report"
    )

    result = compare_revisions(old, new)

    assert result["title_changed"]
    assert not result["content_changed"]


def test_no_content_change():
    old = revision(
        "rev1", "Same content", "same"
    )
    new = revision(
        "rev2", "Same content", "same"
    )

    result = compare_revisions(old, new)

    assert result["added_words"] == 0
    assert result["removed_words"] == 0
    assert result["similarity_ratio"] == 1.0


def test_different_documents_rejected():
    old = revision(
        "rev1", "First", "hash1"
    )
    new = revision(
        "rev2",
        "Second",
        "hash2",
        document_id="doc-2",
    )

    with pytest.raises(ValueError):
        compare_revisions(old, new)


def test_same_revision_rejected():
    old = revision(
        "rev1", "First", "hash1"
    )

    with pytest.raises(ValueError):
        compare_revisions(old, old)


def test_invalid_change_limit():
    old = revision(
        "rev1", "First", "hash1"
    )
    new = revision(
        "rev2", "Second", "hash2"
    )

    with pytest.raises(ValueError):
        compare_revisions(
            old, new, max_changes=0
        )


def test_long_excerpt_is_bounded():
    old = revision(
        "rev1", "Original", "hash1"
    )
    new = revision(
        "rev2",
        " ".join(["newword"] * 100),
        "hash2",
    )

    result = compare_revisions(old, new)

    for change in result["changes"]:
        assert len(
            change["after_excerpt"]
        ) <= 200
