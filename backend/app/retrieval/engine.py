
import asyncio
import math
from dataclasses import dataclass
from typing import Any, Literal

from app.embeddings.indexer import IndexConfig
from app.embeddings.model import (
    EmbeddingProvider,
    validate_vectors,
)
from app.retrieval.bm25 import BM25


SearchMode = Literal[
    "semantic",
    "keyword",
    "hybrid",
]


@dataclass(frozen=True)
class SearchFilters:
    document_type: str | None = None
    source_domain: str | None = None


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    if len(left) != len(right) or not left:
        raise ValueError(
            "Vectors must have equal, nonzero dimensions"
        )

    dot = sum(
        a * b for a, b in zip(left, right)
    )

    magnitude_left = math.sqrt(
        sum(value * value for value in left)
    )

    magnitude_right = math.sqrt(
        sum(value * value for value in right)
    )

    if magnitude_left == 0 or magnitude_right == 0:
        return 0.0

    return dot / (
        magnitude_left * magnitude_right
    )


def rank_scores(
    scores: list[float],
    minimum: float | None = None,
) -> list[int]:
    return sorted(
        (
            index
            for index, score in enumerate(scores)
            if (
                math.isfinite(score)
                and (
                    minimum is None
                    or score > minimum
                )
            )
        ),
        key=lambda i: (-scores[i], i),
    )


def reciprocal_rank_fusion(
    rankings: list[list[str]],
    k: int = 60,
) -> dict[str, float]:
    if k < 1:
        raise ValueError("k must be positive")

    scores: dict[str, float] = {}

    for ranking in rankings:
        # A candidate gets credit only once
        # within each retrieval list.
        seen = set()

        for position, candidate in enumerate(
            ranking,
            start=1,
        ):
            if candidate in seen:
                continue

            seen.add(candidate)

            scores[candidate] = (
                scores.get(candidate, 0.0)
                + 1.0 / (k + position)
            )

    return scores


class RetrievalEngine:
    def __init__(
        self,
        database,
        provider: EmbeddingProvider,
        config: IndexConfig,
        max_candidates: int = 5000,
    ):
        if max_candidates < 1:
            raise ValueError(
                "max_candidates must be positive"
            )

        self.chunks = database["document_chunks"]
        self.provider = provider
        self.config = config
        self.max_candidates = max_candidates

    async def search(
        self,
        query: str,
        mode: SearchMode = "hybrid",
        limit: int = 5,
        filters: SearchFilters | None = None,
    ) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("Search query is empty")

        if mode not in (
            "semantic",
            "keyword",
            "hybrid",
        ):
            raise ValueError("Invalid search mode")

        if not 1 <= limit <= 50:
            raise ValueError(
                "limit must be between 1 and 50"
            )

        filters = filters or SearchFilters()

        mongo_filter: dict[str, Any] = {
            "config_key": self.config.key,
            "embedding_dimension": (
                self.config.dimension
            ),
        }

        if filters.document_type:
            mongo_filter["document_type"] = (
                filters.document_type
            )

        if filters.source_domain:
            mongo_filter["source_domain"] = (
                filters.source_domain
            )

        # Deterministic scan order for reproducible
        # tie-breaking. The extra record detects
        # unsupported oversize scans.
        records = await (
            self.chunks
            .find(mongo_filter)
            .sort("_id", 1)
            .limit(self.max_candidates + 1)
            .to_list(length=self.max_candidates + 1)
        )

        if len(records) > self.max_candidates:
            raise ValueError(
                "Too many candidate chunks; "
                "narrow the metadata filters"
            )

        if not records:
            return []

        # Do not silently search incomplete or
        # malformed embedding records.
        vectors = [
            record.get("embedding")
            for record in records
        ]

        for vector in vectors:
            if not isinstance(vector, list):
                raise ValueError(
                    "Stored embedding is not an array"
                )

        validate_vectors(
            vectors,
            expected_count=len(records),
            dimension=self.config.dimension,
        )

        identifiers = [
            str(record["_id"])
            for record in records
        ]

        semantic_scores = [
            None for _ in records
        ]

        keyword_scores = [
            None for _ in records
        ]

        semantic_ranking: list[int] = []
        keyword_ranking: list[int] = []

        if mode in ("semantic", "hybrid"):
            query_vectors = await asyncio.to_thread(
                self.provider.encode,
                [query],
            )

            validate_vectors(
                query_vectors,
                expected_count=1,
                dimension=self.config.dimension,
            )

            semantic_scores = [
                cosine_similarity(
                    query_vectors[0],
                    vector,
                )
                for vector in vectors
            ]

            # A zero vector is not useful evidence.
            semantic_ranking = rank_scores(
                semantic_scores,
                minimum=0.0,
            )

        if mode in ("keyword", "hybrid"):
            bm25 = BM25([
                (
                    str(record.get("title", ""))
                    + " "
                    + str(record.get("text", ""))
                )
                for record in records
            ])

            keyword_scores = bm25.scores(query)

            # Exclude zero-score keyword matches.
            keyword_ranking = rank_scores(
                keyword_scores,
                minimum=0.0,
            )

        if mode == "semantic":
            final_order = semantic_ranking
            fusion_scores = {}

        elif mode == "keyword":
            final_order = keyword_ranking
            fusion_scores = {}

        else:
            rankings = []

            if semantic_ranking:
                rankings.append([
                    identifiers[i]
                    for i in semantic_ranking
                ])

            if keyword_ranking:
                rankings.append([
                    identifiers[i]
                    for i in keyword_ranking
                ])

            fusion_scores = reciprocal_rank_fusion(
                rankings
            )

            id_to_index = {
                identifier: index
                for index, identifier
                in enumerate(identifiers)
            }

            final_order = [
                id_to_index[identifier]
                for identifier in sorted(
                    fusion_scores,
                    key=lambda identifier: (
                        -fusion_scores[identifier],
                        identifier,
                    ),
                )
            ]

        results = []

        for index in final_order[:limit]:
            record = records[index]
            chunk_id = identifiers[index]

            # A citation identifies its exact stored
            # source and chunk, not a generated claim.
            results.append({
                "rank": len(results) + 1,
                "chunk_id": chunk_id,
                "document_id": record["document_id"],
                "title": record["title"],
                "text": record["text"],
                "source_url": record["source_url"],
                "source_domain": record[
                    "source_domain"
                ],
                "document_type": record[
                    "document_type"
                ],
                "chunk_index": record["chunk_index"],
                "content_hash": record[
                    "content_hash"
                ],
                "config_key": record["config_key"],
                "semantic_score": (
                    semantic_scores[index]
                ),
                "bm25_score": (
                    keyword_scores[index]
                ),
                "hybrid_score": (
                    fusion_scores.get(chunk_id)
                    if mode == "hybrid"
                    else None
                ),
                "citation": {
                    "document_id": record[
                        "document_id"
                    ],
                    "chunk_id": chunk_id,
                    "source_url": record[
                        "source_url"
                    ],
                    "title": record["title"],
                },
            })

        return results
