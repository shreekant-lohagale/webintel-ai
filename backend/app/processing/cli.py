
import argparse
import json
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from app.processing.lineage import (
    DocumentRevision,
    SourceObservation,
    make_observation,
    make_revision,
    merge_observation,
)
from app.processing.normalizer import (
    normalize_article,
    normalize_quote,
)
from app.processing.schemas import WebDocument
from app.processing.similarity import find_near_duplicates


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def read_jsonl(path: Path, model_class) -> dict:
    """Load previously persisted records by their stable ID."""

    if not path.exists():
        return {}

    result = {}

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = model_class.model_validate_json(line)
            except ValidationError as exc:
                raise ValueError(
                    f"Invalid existing data in {path}, "
                    f"line {line_number}"
                ) from exc

            if isinstance(record, WebDocument):
                key = record.document_id
            elif isinstance(record, SourceObservation):
                key = record.observation_id
            else:
                key = record.revision_id

            result[key] = record

    return result


def write_jsonl(path: Path, records: list) -> None:
    """Write JSONL through a temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        for record in records:
            if hasattr(record, "model_dump_json"):
                file.write(record.model_dump_json() + "\n")
            else:
                file.write(
                    json.dumps(record, ensure_ascii=False)
                    + "\n"
                )

    temporary.replace(path)


def process_files(
    input_files: list[tuple],
    output_file: Path,
) -> dict:
    """
    Normalize documents and persist lineage.

    Input format:
      (path, method)                 -> quotes
      (path, method, "article")      -> articles

    Maintains previous CLI compatibility.
    """

    output_file = Path(output_file)

    provenance_file = output_file.with_name(
        "provenance.jsonl"
    )
    revisions_file = output_file.with_name(
        "revisions.jsonl"
    )
    similarities_file = output_file.with_name(
        "near_duplicates.jsonl"
    )

    documents = read_jsonl(output_file, WebDocument)
    observations = read_jsonl(
        provenance_file,
        SourceObservation,
    )
    revisions = read_jsonl(
        revisions_file,
        DocumentRevision,
    )

    # Make revision history available even when migrating
    # from an older documents-only export.
    for existing in documents.values():
        revision = make_revision(existing)
        revisions.setdefault(revision.revision_id, revision)

    stats = Counter()
    errors = []
    seen_in_batch = set()

    for input_spec in input_files:
        if len(input_spec) == 2:
            input_path, method = input_spec
            document_type = "quote"
        elif len(input_spec) == 3:
            input_path, method, document_type = input_spec
        else:
            raise ValueError(
                "Input tuple must have 2 or 3 elements"
            )

        input_path = Path(input_path)

        with input_path.open(
            "r", encoding="utf-8"
        ) as file:
            raw_records = json.load(file)

        if not isinstance(raw_records, list):
            raise ValueError(
                f"Expected JSON array: {input_path}"
            )

        for index, record in enumerate(raw_records):
            stats["input_records"] += 1

            try:
                if not isinstance(record, dict):
                    raise ValueError(
                        "Input record must be an object"
                    )

                if document_type == "quote":
                    document = normalize_quote(
                        record,
                        extraction_method=method,
                    )
                elif document_type == "article":
                    document = normalize_article(
                        record,
                        extraction_method=method,
                    )
                else:
                    raise ValueError(
                        f"Unsupported document type: {document_type}"
                    )

            except (
                ValidationError,
                ValueError,
                KeyError,
                TypeError,
            ) as exc:
                stats["invalid_records"] += 1

                errors.append({
                    "file": input_path.name,
                    "record_index": index,
                    "error": str(exc),
                })
                continue

            doc_id = document.document_id

            # Count duplicates within this processing run.
            if doc_id in seen_in_batch:
                stats["duplicate_records"] += 1
            else:
                seen_in_batch.add(doc_id)

            # Keep the newest document as the current state.
            previous = documents.get(doc_id)

            if (
                previous is None
                or document.scraped_at > previous.scraped_at
            ):
                documents[doc_id] = document

            # Every unique source/method/content combination
            # becomes a source observation.
            observation = make_observation(document)

            previous_observation = observations.get(
                observation.observation_id
            )

            if previous_observation:
                observations[observation.observation_id] = (
                    merge_observation(
                        previous_observation,
                        observation,
                    )
                )
            else:
                observations[
                    observation.observation_id
                ] = observation

            # Preserve one revision per ID + content hash.
            revision = make_revision(document)

            existing_revision = revisions.get(
                revision.revision_id
            )

            if (
                existing_revision is None
                or revision.observed_at
                < existing_revision.observed_at
            ):
                revisions[revision.revision_id] = revision

    near_duplicates = find_near_duplicates(
        list(documents.values()),
        threshold=0.80,
        minimum_tokens=12,
    )

    write_jsonl(
        output_file,
        sorted(
            documents.values(),
            key=lambda doc: doc.document_id,
        ),
    )

    write_jsonl(
        provenance_file,
        sorted(
            observations.values(),
            key=lambda obs: obs.observation_id,
        ),
    )

    write_jsonl(
        revisions_file,
        sorted(
            revisions.values(),
            key=lambda rev: rev.revision_id,
        ),
    )

    write_jsonl(
        similarities_file,
        near_duplicates,
    )

    return {
        "input_records": stats["input_records"],
        "unique_documents": len(documents),
        "duplicate_records": stats["duplicate_records"],
        "invalid_records": stats["invalid_records"],
        "source_observations": len(observations),
        "document_revisions": len(revisions),
        "near_duplicate_pairs": len(near_duplicates),
        "output_file": str(output_file),
        "provenance_file": str(provenance_file),
        "revisions_file": str(revisions_file),
        "similarities_file": str(similarities_file),
        "sample_errors": errors[:10],
    }


def main():
    parser = argparse.ArgumentParser(
        description="WebIntel AI document processing"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "processed" / "documents.jsonl",
    )

    parser.add_argument(
        "--articles",
        type=Path,
        default=None,
        help="Optional JSON array of extracted articles",
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

    if args.articles is not None:
        inputs.append(
            (args.articles, "scrapy", "article")
        )

    for input_spec in inputs:
        path = Path(input_spec[0])

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
