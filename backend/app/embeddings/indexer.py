
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING

from app.embeddings.chunker import (
    CHUNKER_VERSION,
    chunk_text,
    make_chunk_id,
)
from app.embeddings.model import (
    EMBEDDING_DIMENSION,
    EmbeddingProvider,
    validate_vectors,
)


@dataclass(frozen=True)
class IndexConfig:
    model_id: str
    model_revision: str
    chunk_words: int = 120
    overlap_words: int = 25
    dimension: int = EMBEDDING_DIMENSION

    def __post_init__(self):
        if not self.model_id.strip():
            raise ValueError("model_id is required")

        if not self.model_revision.strip():
            raise ValueError(
                "model_revision is required"
            )

        if self.chunk_words < 1:
            raise ValueError(
                "chunk_words must be positive"
            )

        if not 0 <= self.overlap_words < self.chunk_words:
            raise ValueError(
                "Invalid chunk overlap"
            )

        if self.dimension < 1:
            raise ValueError(
                "dimension must be positive"
            )

    @property
    def key(self) -> str:
        settings = {
            "chunker": CHUNKER_VERSION,
            "chunk_words": self.chunk_words,
            "overlap_words": self.overlap_words,
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "dimension": self.dimension,
        }

        encoded = json.dumps(
            settings,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            encoded.encode("utf-8")
        ).hexdigest()


class DocumentChunkIndexer:
    def __init__(
        self,
        database,
        provider: EmbeddingProvider,
        config: IndexConfig,
        batch_size: int = 16,
    ):
        if batch_size < 1:
            raise ValueError(
                "batch_size must be positive"
            )

        self.database = database
        self.documents = database["documents"]
        self.chunks = database["document_chunks"]

        self.provider = provider
        self.config = config
        self.batch_size = batch_size

    async def ensure_indexes(self):
        await self.chunks.create_index([
            ("document_id", ASCENDING),
            ("config_key", ASCENDING),
        ])

        await self.chunks.create_index([
            ("config_key", ASCENDING),
            ("source_domain", ASCENDING),
        ])

        await self.chunks.create_index([
            ("config_key", ASCENDING),
            ("document_type", ASCENDING),
        ])

    def prepare_chunks(
        self,
        document: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Generate chunk metadata for a current
        source document without embedding yet.
        """

        document_id = document["document_id"]
        content_hash = document["content_hash"]

        chunks = chunk_text(
            document["content"],
            chunk_words=self.config.chunk_words,
            overlap_words=self.config.overlap_words,
        )

        prepared = []

        for chunk in chunks:
            chunk_id = make_chunk_id(
                document_id=document_id,
                content_hash=content_hash,
                chunk_index=chunk.chunk_index,
                chunk_hash=chunk.chunk_hash,
                config_key=self.config.key,
            )

            prepared.append({
                "_id": chunk_id,
                "document_id": document_id,
                "content_hash": content_hash,
                "config_key": self.config.key,
                "chunker_version": CHUNKER_VERSION,
                "chunk_index": chunk.chunk_index,
                "chunk_hash": chunk.chunk_hash,
                "word_start": chunk.word_start,
                "word_end": chunk.word_end,
                "text": chunk.text,
                "title": document["title"],
                "source_url": str(
                    document["source_url"]
                ),
                "source_domain": document[
                    "source_domain"
                ],
                "document_type": document[
                    "document_type"
                ],
                "model_id": self.config.model_id,
                "model_revision": (
                    self.config.model_revision
                ),
                "embedding_dimension": (
                    self.config.dimension
                ),
            })

        return prepared

    async def index_document(
        self,
        document: dict[str, Any],
    ) -> dict[str, int]:
        """
        Incrementally index a single document.

        New vectors are written before stale vectors
        are removed. Existing current vectors are
        reused when identities are unchanged.
        """

        prepared = self.prepare_chunks(document)

        scope = {
            "document_id": document["document_id"],
            "config_key": self.config.key,
        }

        existing = await self.chunks.find(
            scope,
            {"_id": 1, "embedding": 1},
        ).to_list(length=None)

        valid_existing_ids = {
            record["_id"]
            for record in existing
            if (
                isinstance(
                    record.get("embedding"),
                    list,
                )
                and len(record["embedding"])
                == self.config.dimension
            )
        }

        all_ids = {
            record["_id"]
            for record in prepared
        }

        missing = [
            record
            for record in prepared
            if record["_id"]
            not in valid_existing_ids
        ]

        inserted = 0

        # Compute and validate all new embeddings
        # before making any changes to MongoDB.
        new_vectors = []

        for offset in range(
            0,
            len(missing),
            self.batch_size,
        ):
            batch = missing[
                offset:offset + self.batch_size
            ]

            vectors = self.provider.encode([
                item["text"]
                for item in batch
            ])

            validate_vectors(
                vectors,
                expected_count=len(batch),
                dimension=self.config.dimension,
            )

            new_vectors.extend(vectors)

        for record, vector in zip(
            missing,
            new_vectors,
        ):
            stored = {
                **record,
                "embedding": vector,
                "indexed_at": datetime.now(
                    timezone.utc
                ),
            }

            await self.chunks.replace_one(
                {"_id": record["_id"]},
                stored,
                upsert=True,
            )

            inserted += 1

        # Remove old document revisions/chunks
        # only after the current vectors are stored.
        deletion_filter = {
            **scope,
            "_id": {"$nin": list(all_ids)},
        }

        deleted = await self.chunks.delete_many(
            deletion_filter
        )

        return {
            "total_chunks": len(prepared),
            "embedded": inserted,
            "reused": len(prepared) - inserted,
            "deleted": deleted.deleted_count,
        }

    async def index_all(
        self,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Index source documents sequentially.

        This prevents excessive CPU/memory usage
        on a development machine.
        """

        if limit is not None and limit < 1:
            raise ValueError(
                "limit must be positive"
            )

        summary = {
            "documents": 0,
            "chunks": 0,
            "embedded": 0,
            "reused": 0,
            "deleted": 0,
            "config_key": self.config.key,
            "model_id": self.config.model_id,
            "model_revision": (
                self.config.model_revision
            ),
        }

        cursor = self.documents.find().sort(
            "_id",
            ASCENDING,
        )

        if limit is not None:
            cursor = cursor.limit(limit)

        async for document in cursor:
            result = await self.index_document(
                document
            )

            summary["documents"] += 1
            summary["chunks"] += result[
                "total_chunks"
            ]
            summary["embedded"] += result[
                "embedded"
            ]
            summary["reused"] += result[
                "reused"
            ]
            summary["deleted"] += result[
                "deleted"
            ]

        return summary
