
import re
from difflib import SequenceMatcher
from typing import Any


def tokens(text: str) -> list[str]:
    """
    Tokenize words independently of punctuation.

    Examples:
    "workflows." -> ["workflows"]
    "automation." -> ["automation"]
    """
    return re.findall(
        r"\b\w+(?:['’\-]\w+)*\b",
        text,
        flags=re.UNICODE,
    )


def excerpt(
    values: list[str],
    max_chars: int = 200,
) -> str:
    text = " ".join(values)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def compare_revisions(
    before: dict[str, Any],
    after: dict[str, Any],
    max_changes: int = 30,
) -> dict[str, Any]:
    if before["document_id"] != after["document_id"]:
        raise ValueError(
            "Cannot compare different documents"
        )

    if before["revision_id"] == after["revision_id"]:
        raise ValueError(
            "Select two distinct revisions"
        )

    if not 1 <= max_changes <= 100:
        raise ValueError(
            "max_changes must be between 1 and 100"
        )

    old_words = tokens(before.get("content", ""))
    new_words = tokens(after.get("content", ""))

    matcher = SequenceMatcher(
        None,
        old_words,
        new_words,
        autojunk=False,
    )

    changes = []
    added_words = 0
    removed_words = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        removed = i2 - i1
        added = j2 - j1

        removed_words += removed
        added_words += added

        if len(changes) < max_changes:
            changes.append({
                "kind": tag,
                "before_excerpt": excerpt(
                    old_words[i1:i2]
                ),
                "after_excerpt": excerpt(
                    new_words[j1:j2]
                ),
                "removed_words": removed,
                "added_words": added,
            })

    title_changed = (
        before.get("title", "")
        != after.get("title", "")
    )

    content_changed = (
        before["content_hash"]
        != after["content_hash"]
    )

    if content_changed:
        description = (
            f"Content changed: {added_words} words "
            f"added and {removed_words} words removed."
        )
    else:
        description = "No content hash change."

    if title_changed:
        description += " Title also changed."

    return {
        "document_id": before["document_id"],
        "from_revision_id": before["revision_id"],
        "to_revision_id": after["revision_id"],
        "from_observed_at": before["observed_at"],
        "to_observed_at": after["observed_at"],
        "from_content_hash": before["content_hash"],
        "to_content_hash": after["content_hash"],
        "content_changed": content_changed,
        "title_changed": title_changed,
        "before_title": before.get("title", ""),
        "after_title": after.get("title", ""),
        "before_word_count": len(old_words),
        "after_word_count": len(new_words),
        "added_words": added_words,
        "removed_words": removed_words,
        "similarity_ratio": round(
            matcher.ratio(), 4
        ),
        "change_summary": description,
        "changes": changes,
        "changes_truncated": (
            len([
                op for op in matcher.get_opcodes()
                if op[0] != "equal"
            ]) > max_changes
        ),
    }
