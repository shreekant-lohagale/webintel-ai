
import hashlib
import re
from dataclasses import dataclass


CHUNKER_VERSION = "word-window-v1"


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    text: str
    word_start: int
    word_end: int
    chunk_hash: str


def sha256(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def normalize_for_chunks(text: str) -> str:
    """
    Normalize whitespace consistently.

    Preserve punctuation and Unicode text.
    """
    return " ".join(text.split())


def chunk_text(
    text: str,
    chunk_words: int = 120,
    overlap_words: int = 25,
) -> list[TextChunk]:
    if chunk_words < 1:
        raise ValueError(
            "chunk_words must be positive"
        )

    if overlap_words < 0:
        raise ValueError(
            "overlap_words cannot be negative"
        )

    if overlap_words >= chunk_words:
        raise ValueError(
            "overlap_words must be smaller "
            "than chunk_words"
        )

    cleaned = normalize_for_chunks(text)
    words = cleaned.split()

    if not words:
        return []

    step = chunk_words - overlap_words
    results = []

    for start in range(0, len(words), step):
        end = min(
            start + chunk_words,
            len(words),
        )

        content = " ".join(words[start:end])

        results.append(
            TextChunk(
                chunk_index=len(results),
                text=content,
                word_start=start,
                word_end=end,
                chunk_hash=sha256(content),
            )
        )

        if end == len(words):
            break

    return results


def make_chunk_id(
    document_id: str,
    content_hash: str,
    chunk_index: int,
    chunk_hash: str,
    config_key: str,
) -> str:
    """
    Stable identity across repeated indexing runs.

    Changes to content/config produce new identities.
    """
    identity = "\n".join([
        document_id,
        content_hash,
        str(chunk_index),
        chunk_hash,
        config_key,
    ])

    return sha256(identity)
