
import argparse
import asyncio
import json
from pathlib import Path

from app.pipeline.run import (
    DEFAULT_START_URL,
    run_pipeline,
    validate_start_url,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
RESULT_MARKER = "WEBINTEL_RESULT_JSON="


async def execute(
    job_id: str,
    database_name: str,
    browser: bool,
) -> dict:
    """
    Execute one local, approved crawl.

    The parent worker controls the subprocess
    lifetime and handles cancellation.
    """

    validate_start_url(
        DEFAULT_START_URL,
        allow_live=False,
    )

    output_directory = (
        BACKEND_ROOT
        / "data"
        / "processed"
        / "jobs"
        / job_id
    )

    return await run_pipeline(
        start_url=DEFAULT_START_URL,
        browser=browser,
        allow_live=False,
        output_directory=output_directory,
        database_name=database_name,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--job-id",
        required=True,
    )

    parser.add_argument(
        "--database",
        required=True,
    )

    parser.add_argument(
        "--browser",
        action="store_true",
    )

    args = parser.parse_args()

    report = asyncio.run(
        execute(
            job_id=args.job_id,
            database_name=args.database,
            browser=args.browser,
        )
    )

    # Dedicated marker lets the parent distinguish
    # the result from regular subprocess output.
    print(
        RESULT_MARKER
        + json.dumps(report, default=str),
        flush=True,
    )


if __name__ == "__main__":
    main()
