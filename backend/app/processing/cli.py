
import argparse
import json
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from app.processing.normalizer import normalize_quote


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def process_files(
    input_files: list[tuple[Path, str]],
    output_file: Path,
) -> dict:
    """Normalize, validate and deduplicate raw records."""

    documents = {}
    stats = Counter()
    errors = []

    for input_path, method in input_files:
        with input_path.open("r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            raise ValueError(
                f"Expected JSON array in {input_path}"
            )

        for index, record in enumerate(records):
            stats["input_records"] += 1

            try:
                if not isinstance(record, dict):
                    raise ValueError("Record must be an object")

                document = normalize_quote(
                    record,
                    extraction_method=method,
                )

                if document.document_id in documents:
                    stats["duplicate_records"] += 1

                    # Keep the earliest valid observation,
                    # rather than overwriting source metadata.
                    existing = documents[document.document_id]

                    if document.scraped_at < existing.scraped_at:
                        documents[document.document_id] = document

                    continue

                documents[document.document_id] = document

            except (
                ValueError,
                KeyError,
                TypeError,
                ValidationError,
            ) as exc:
                stats["invalid_records"] += 1

                errors.append({
                    "file": input_path.name,
                    "record_index": index,
                    "error": str(exc),
                })

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Write once after successful in-memory processing.
    temp_file = output_file.with_suffix(
        output_file.suffix + ".tmp"
    )

    with temp_file.open("w", encoding="utf-8") as file:
        for document in sorted(
            documents.values(),
            key=lambda item: item.document_id,
        ):
            file.write(
                document.model_dump_json()
                + "\n"
            )

    temp_file.replace(output_file)

    stats["unique_documents"] = len(documents)

    report = {
        "input_records": stats["input_records"],
        "unique_documents": stats["unique_documents"],
        "duplicate_records": stats["duplicate_records"],
        "invalid_records": stats["invalid_records"],
        "output_file": str(output_file),
        "sample_errors": errors[:10],
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="WebIntel AI document normalization"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "processed" / "documents.jsonl",
    )

    args = parser.parse_args()

    inputs = [
        (
            DATA_DIR / "raw" / "quotes.json",
            "scrapy",
        ),
        (
            DATA_DIR / "raw" / "dynamic_quotes.json",
            "playwright",
        ),
    ]

    for path, _ in inputs:
        if not path.is_file():
            parser.error(
                f"Missing input file: {path}"
            )

    report = process_files(
        input_files=inputs,
        output_file=args.output,
    )

    print(json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
