
import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest

from app.pipeline.run import (
    ingest_articles,
    run_crawler,
)
from app.storage.mongodb import create_client
from app.storage.repository import MongoRepository
from mock_site.article_server import create_server


pytestmark = pytest.mark.skipif(
    os.getenv("WEBINTEL_RUN_MONGO_TESTS") != "1",
    reason="MongoDB integration tests are opt-in",
)


async def exercise_end_to_end():
    server = create_server(
        host="127.0.0.1",
        port=0,
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"

    client = create_client()
    database_name = (
        "webintel_ai_article_test_"
        + uuid4().hex
    )

    try:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            raw_path = root / "raw" / "articles.json"
            output_directory = root / "processed"

            first_records = await asyncio.to_thread(
                run_crawler,
                url,
                raw_path,
                False,
            )

            assert len(first_records) == 2

            first_report = await ingest_articles(
                input_path=raw_path,
                output_directory=output_directory,
                database_name=database_name,
            )

            counts = first_report["mongodb"]["database_counts"]

            assert counts["documents"] == 2
            assert counts["document_revisions"] == 2
            assert counts["source_observations"] == 2

            # Importing the SAME snapshot must be a no-op
            # for current-document writes.
            repeated = await ingest_articles(
                input_path=raw_path,
                output_directory=output_directory,
                database_name=database_name,
            )

            assert (
                repeated["mongodb"]
                ["current_documents_written"] == 0
            )

            # Change one article in the local test server.
            request = Request(
                f"http://127.0.0.1:{port}/test/advance",
                data=b"",
                method="POST",
            )

            await asyncio.to_thread(
                lambda: urlopen(
                    request, timeout=5
                ).read()
            )

            updated_records = await asyncio.to_thread(
                run_crawler,
                url,
                raw_path,
                False,
            )

            assert len(updated_records) == 2

            updated_report = await ingest_articles(
                input_path=raw_path,
                output_directory=output_directory,
                database_name=database_name,
            )

            counts = updated_report["mongodb"]["database_counts"]

            # Same two logical article URLs.
            assert counts["documents"] == 2

            # One updated content version.
            assert counts["document_revisions"] == 3

            repository = MongoRepository(
                client[database_name]
            )

            documents = await repository.list_documents(
                limit=10
            )

            assert len(documents) == 2

            ai_doc = next(
                doc
                for doc in documents
                if "AI Workflows" in doc.title
            )

            revisions = await repository.get_revisions(
                ai_doc.document_id
            )

            assert len(revisions) == 2

            assert any(
                "human review" in rev.content
                for rev in revisions
            )

    finally:
        # Generated unique database name.
        # Never drop the development database.
        try:
            await client.drop_database(database_name)
        finally:
            await client.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def test_article_pipeline_end_to_end():
    asyncio.run(exercise_end_to_end())
