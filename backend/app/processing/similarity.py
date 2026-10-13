
import re
import unicodedata

from app.processing.schemas import WebDocument


def tokenize(text: str) -> list[str]:
    """Create normalized tokens for similarity checks."""

    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()

    return re.findall(r"\w+", text, flags=re.UNICODE)


def word_shingles(
    text: str,
    size: int = 3,
) -> set[tuple[str, ...]]:
    if size < 1:
        raise ValueError("Shingle size must be >= 1")

    tokens = tokenize(text)

    if len(tokens) < size:
        return set()

    return {
        tuple(tokens[index:index + size])
        for index in range(len(tokens) - size + 1)
    }


def jaccard_similarity(
    first: str,
    second: str,
    shingle_size: int = 3,
) -> float:
    a = word_shingles(first, shingle_size)
    b = word_shingles(second, shingle_size)

    if not a or not b:
        return 0.0

    return len(a & b) / len(a | b)


def find_near_duplicates(
    documents: list[WebDocument],
    threshold: float = 0.80,
    minimum_tokens: int = 12,
    shingle_size: int = 3,
) -> list[dict]:
    """
    Link similar articles without merging their identities.

    Intended for small to medium test batches.
    """

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Threshold must be between 0 and 1")

    if minimum_tokens < shingle_size:
        raise ValueError(
            "minimum_tokens must be >= shingle_size"
        )

    articles = sorted(
        [
            document
            for document in documents
            if document.document_type == "article"
            and len(tokenize(document.content)) >= minimum_tokens
        ],
        key=lambda document: document.document_id,
    )

    results = []

    for i, first in enumerate(articles):
        for second in articles[i + 1:]:
            if first.document_id == second.document_id:
                continue

            score = jaccard_similarity(
                first.content,
                second.content,
                shingle_size=shingle_size,
            )

            if score >= threshold:
                results.append({
                    "document_id_a": first.document_id,
                    "document_id_b": second.document_id,
                    "similarity_score": round(score, 6),
                    "method": f"word_jaccard_{shingle_size}",
                })

    return results
