
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from app.processing.cli import process_files
from app.storage.import_cli import import_snapshots
from app.storage.mongodb import create_client
from app.storage.repository import MongoRepository


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_START_URL = "http://127.0.0.1:8766/"


def validate_start_url(url, allow_live=False):
    """Restrict unattended crawling to the local test site."""

    parts = urlsplit(url)

    if parts.username or parts.password or parts.fragment:
        raise ValueError(
            "Credentials and URL fragments are not allowed"
        )

    if parts.scheme not in ("http", "https"):
        raise ValueError("Unsupported URL scheme")

    if not parts.hostname:
        raise ValueError("Missing hostname")

    local = (
        parts.scheme == "http"
        and parts.hostname == "127.0.0.1"
        and parts.port == 8766
        and parts.path in ("", "/")
        and not parts.query
    )

    if local:
        return "local"

    if not allow_live:
        raise ValueError(
            "External crawling is disabled. "
            "Use --allow-live only for a specifically "
            "approved public source."
        )

    if parts.scheme != "https":
        raise ValueError("Live crawling requires HTTPS")

    if parts.port not in (None, 443):
        raise ValueError("Nonstandard live ports are not allowed")

    if parts.query:
        raise ValueError("Use an index URL without query parameters")

    # Require an explicit hostname allowlist as a second
    # control, not just the --allow-live flag.
    allowed_hosts = {
        item.strip().lower()
        for item in os.getenv(
            "WEBINTEL_ALLOWED_HOSTS", ""
        ).split(",")
        if item.strip()
    }

    if parts.hostname.lower() not in allowed_hosts:
        raise ValueError(
            "Hostname is not in WEBINTEL_ALLOWED_HOSTS"
        )

    return "live"


def run_crawler(start_url, raw_path, browser=False):
    """Launch Scrapy in its own subprocess."""

    raw_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "articles",
        "-a",
        f"start_url={start_url}",
        "-a",
        f"browser={int(browser)}",
        "-O",
        str(raw_path),
    ]

    if browser:
        command.extend([
            "-s",
            "WEBINTEL_ARTICLE_BROWSER=1",
        ])

    result = subprocess.run(
        command,
        cwd=BACKEND_ROOT,
        check=False,
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Scrapy exited with code {result.returncode}"
        )

    if not raw_path.exists():
        raise RuntimeError("Scrapy did not create an output file")

    with raw_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list) or not records:
        raise RuntimeError(
            "Crawler exported no articles; ingestion cancelled"
        )

    return records


async def ingest_articles(
    input_path: Path,
    output_directory: Path,
    database_name: str,
    method: str = "scrapy",
):
    """Normalize article records and persist them to MongoDB."""

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_directory / "documents.jsonl"

    processing_report = process_files(
        [(input_path, method, "article")],
        output_file,
    )

    client = create_client()

    try:
        await client.admin.command("ping")

        repository = MongoRepository(
            client[database_name]
        )

        import_report = await import_snapshots(
            repository,
            output_directory,
        )

        sample_documents = await repository.list_documents(
            limit=5
        )

        return {
            "processing": processing_report,
            "mongodb": import_report,
            "sample_titles": [
                document.title
                for document in sample_documents
            ],
        }

    finally:
        await client.close()


async def run_pipeline(
    start_url: str,
    browser: bool = False,
    allow_live: bool = False,
    output_directory: Path | None = None,
    database_name: str | None = None,
):
    mode = validate_start_url(start_url, allow_live)

    if output_directory is None:
        output_directory = (
            BACKEND_ROOT
            / "data"
            / "processed"
            / (
                "article_live"
                if mode == "live"
                else "article_mock"
            )
        )

    if database_name is None:
        database_name = (
            "webintel_ai"
            if mode == "live"
            else "webintel_ai_article_dev"
        )

    # Do not accidentally write local mock articles
    # into the primary production-oriented database.
    if (
        mode == "local"
        and database_name == "webintel_ai"
    ):
        raise ValueError(
            "The local mock pipeline cannot use webintel_ai"
        )

    raw_path = (
        output_directory
        / "raw"
        / "articles.json"
    )

    articles = await asyncio.to_thread(
        run_crawler,
        start_url,
        raw_path,
        browser,
    )

    report = await ingest_articles(
        input_path=raw_path,
        output_directory=output_directory,
        database_name=database_name,
        method="playwright" if browser else "scrapy",
    )

    return {
        "mode": mode,
        "database": database_name,
        "crawled_articles": len(articles),
        **report,
    }


def main():
    parser = argparse.ArgumentParser(
        description="WebIntel AI article ingestion pipeline"
    )

    parser.add_argument(
        "--start-url",
        default=DEFAULT_START_URL,
    )

    parser.add_argument(
        "--browser",
        action="store_true",
        help="Render using Chromium and Playwright",
    )

    parser.add_argument(
        "--allow-live",
        action="store_true",
        help="Permit an explicitly allowlisted HTTPS source",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--database",
        default=None,
    )

    args = parser.parse_args()

    report = asyncio.run(
        run_pipeline(
            start_url=args.start_url,
            browser=args.browser,
            allow_live=args.allow_live,
            output_directory=args.output_dir,
            database_name=args.database,
        )
    )

    print(json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
