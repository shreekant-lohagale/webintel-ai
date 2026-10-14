
import pytest

from app.evaluation.metrics import (
    aggregate_metrics,
    evaluate_retrieval,
)


def test_perfect_top_one():
    result = evaluate_retrieval(
        ["doc-a", "doc-b"],
        ["doc-a"],
        k=1,
    )

    assert result.precision_at_k == 1.0
    assert result.recall_at_k == 1.0
    assert result.reciprocal_rank == 1.0


def test_relevant_document_second():
    result = evaluate_retrieval(
        ["doc-b", "doc-a"],
        ["doc-a"],
        k=2,
    )

    assert result.precision_at_k == 0.5
    assert result.recall_at_k == 1.0
    assert result.reciprocal_rank == 0.5


def test_missing_relevant_document():
    result = evaluate_retrieval(
        ["doc-b"],
        ["doc-a"],
        k=2,
    )

    assert result.precision_at_k == 0
    assert result.recall_at_k == 0
    assert result.reciprocal_rank == 0


def test_duplicate_document_not_counted_twice():
    result = evaluate_retrieval(
        ["doc-a", "doc-a", "doc-b"],
        ["doc-a", "doc-b"],
        k=2,
    )

    assert result.precision_at_k == 1.0
    assert result.recall_at_k == 1.0


def test_macro_average():
    first = evaluate_retrieval(
        ["a"], ["a"], k=1
    )
    second = evaluate_retrieval(
        ["b"], ["a"], k=1
    )

    summary = aggregate_metrics([
        first, second
    ])

    assert summary["precision_at_k"] == 0.5
    assert summary["recall_at_k"] == 0.5
    assert summary["mrr"] == 0.5


def test_no_positive_qrels_rejected():
    with pytest.raises(ValueError):
        evaluate_retrieval(
            ["a"], [], k=2
        )


def test_invalid_k():
    with pytest.raises(ValueError):
        evaluate_retrieval(
            ["a"], ["a"], k=0
        )
