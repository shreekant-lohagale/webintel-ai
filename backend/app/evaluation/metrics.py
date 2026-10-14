
from dataclasses import dataclass
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class RetrievalMetrics:
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float


def unique_ordered(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


def evaluate_retrieval(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int = 5,
) -> RetrievalMetrics:
    if k < 1:
        raise ValueError("k must be positive")

    if not relevant_ids:
        raise ValueError(
            "Retrieval relevance metrics require "
            "at least one positive gold label"
        )

    relevant = set(relevant_ids)
    ranked = unique_ordered(retrieved_ids)[:k]

    hits = sum(
        document_id in relevant
        for document_id in ranked
    )

    precision = hits / k
    recall = hits / len(relevant)

    reciprocal_rank = 0.0

    for position, document_id in enumerate(
        ranked,
        start=1,
    ):
        if document_id in relevant:
            reciprocal_rank = 1.0 / position
            break

    return RetrievalMetrics(
        precision_at_k=precision,
        recall_at_k=recall,
        reciprocal_rank=reciprocal_rank,
    )


def aggregate_metrics(
    results: list[RetrievalMetrics],
) -> dict[str, float]:
    if not results:
        raise ValueError(
            "No evaluable retrieval results"
        )

    return {
        "precision_at_k": mean(
            item.precision_at_k for item in results
        ),
        "recall_at_k": mean(
            item.recall_at_k for item in results
        ),
        "mrr": mean(
            item.reciprocal_rank for item in results
        ),
    }
