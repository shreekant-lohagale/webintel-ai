
import pytest

from app.retrieval.bm25 import BM25, tokenize
from app.retrieval.engine import (
    cosine_similarity,
    rank_scores,
    reciprocal_rank_fusion,
)


def test_tokenize_is_case_insensitive():
    assert tokenize("AI and DATA!") == [
        "ai", "and", "data"
    ]


def test_bm25_prefers_keyword_match():
    corpus = [
        "Python data processing pipelines",
        "Cloud infrastructure monitoring",
        "Data processing with Python",
    ]

    scores = BM25(corpus).scores(
        "Python processing"
    )

    assert scores[0] > scores[1]
    assert scores[2] > scores[1]


def test_bm25_handles_empty_corpus():
    assert BM25([]).scores("AI") == []


def test_bm25_unmatched_query_is_zero():
    scores = BM25([
        "machine learning",
        "database systems",
    ]).scores("unrelatedkeyword")

    assert scores == [0.0, 0.0]


def test_identical_vectors_have_cosine_one():
    assert cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0],
    ) == pytest.approx(1.0)


def test_orthogonal_vectors_have_cosine_zero():
    assert cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    ) == pytest.approx(0.0)


def test_opposite_vectors_have_negative_cosine():
    assert cosine_similarity(
        [1.0, 0.0],
        [-1.0, 0.0],
    ) == pytest.approx(-1.0)


def test_invalid_cosine_dimension():
    with pytest.raises(ValueError):
        cosine_similarity([1.0], [1.0, 2.0])


def test_rank_scores_excludes_zero():
    assert rank_scores(
        [0.0, 0.7, 0.2, -0.1],
        minimum=0.0,
    ) == [1, 2]


def test_rrf_rewards_multiple_rankings():
    scores = reciprocal_rank_fusion([
        ["a", "b", "c"],
        ["b", "a", "d"],
    ])

    assert scores["a"] > scores["c"]
    assert scores["b"] > scores["d"]


def test_rrf_deduplicates_within_ranking():
    scores = reciprocal_rank_fusion([
        ["a", "a", "b"],
    ])

    assert scores["a"] == pytest.approx(1 / 61)


def test_invalid_rrf_constant():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(
            [["a"]],
            k=0,
        )
