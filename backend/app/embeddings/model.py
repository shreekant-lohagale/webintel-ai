
import math
from typing import Protocol, Sequence


MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


class EmbeddingProvider(Protocol):
    def encode(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        ...


def validate_vectors(
    vectors: list[list[float]],
    expected_count: int,
    dimension: int,
) -> None:
    if len(vectors) != expected_count:
        raise ValueError(
            "Embedding count does not match "
            "input text count"
        )

    for vector in vectors:
        if len(vector) != dimension:
            raise ValueError(
                "Unexpected embedding dimension"
            )

        if not all(
            math.isfinite(float(value))
            for value in vector
        ):
            raise ValueError(
                "Embedding contains NaN or infinity"
            )


class SentenceTransformerProvider:
    """
    Local CPU embedding model.

    Import is deferred so unit tests do not
    need to initialize PyTorch.
    """

    def __init__(
        self,
        model_id: str = MODEL_ID,
        revision: str = "main",
        batch_size: int = 16,
    ):
        from sentence_transformers import (
            SentenceTransformer,
        )

        if batch_size < 1:
            raise ValueError(
                "batch_size must be positive"
            )

        self.batch_size = batch_size

        self.model = SentenceTransformer(
            model_id,
            revision=revision,
            device="cpu",
        )

        dimension = (
            self.model.get_sentence_embedding_dimension()
        )

        if dimension != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSION} "
                f"dimensions, got {dimension}"
            )

    def encode(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        vectors = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return [
            [float(value) for value in row]
            for row in vectors
        ]
