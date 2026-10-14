
import argparse
import asyncio
import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv

from app.embeddings.model import SentenceTransformerProvider
from app.evaluation.groundedness import (
    evaluate_groundedness,
)
from app.evaluation.metrics import (
    aggregate_metrics,
    evaluate_retrieval,
)
from app.rag.provider import GroqProvider
from app.rag.schemas import AskRequest
from app.rag.service import RAGService
from app.retrieval.cli import retrieval_config
from app.retrieval.engine import (
    RetrievalEngine,
    SearchFilters,
)
from app.storage.mongodb import create_client


def milliseconds(start: float) -> float:
    return round(
        (time.perf_counter() - start) * 1000,
        3,
    )


async def timed_search(
    engine,
    question,
    mode,
    limit,
    filters,
):
    started = time.perf_counter()

    results = await engine.search(
        query=question,
        mode=mode,
        limit=limit,
        filters=filters,
    )

    return results, milliseconds(started)


def check_dataset(dataset):
    if not isinstance(dataset.get("cases"), list):
        raise ValueError(
            "Dataset must contain cases"
        )

    seen = set()

    for case in dataset["cases"]:
        required = {
            "id",
            "question",
            "mode",
            "relevant_document_ids",
            "expected_behavior",
        }

        if not required.issubset(case):
            raise ValueError(
                "Missing required evaluation field"
            )

        if case["id"] in seen:
            raise ValueError(
                "Duplicate evaluation case ID"
            )

        if case["mode"] not in (
            "semantic", "keyword", "hybrid"
        ):
            raise ValueError("Invalid evaluation mode")

        if case["expected_behavior"] not in (
            "answered", "abstained"
        ):
            raise ValueError(
                "Invalid expected behavior"
            )

        seen.add(case["id"])


async def evaluate(args):
    load_dotenv()

    dataset = json.loads(
        Path(args.dataset).read_text(
            encoding="utf-8"
        )
    )

    check_dataset(dataset)

    database_name = dataset["database"]
    config = retrieval_config()

    report = {
        "dataset_id": dataset["dataset_id"],
        "database": database_name,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "config_key": config.key,
        "embedding_model": config.model_id,
        "embedding_revision": config.model_revision,
        "k": args.k,
        "live_llm": args.live_llm,
        "cases": [],
    }

    load_started = time.perf_counter()

    provider = await asyncio.to_thread(
        SentenceTransformerProvider,
        model_id=config.model_id,
        revision=config.model_revision,
        batch_size=16,
    )

    report["model_load_ms"] = milliseconds(
        load_started
    )

    client = create_client()

    try:
        await client.admin.command("ping")

        database = client[database_name]

        engine = RetrievalEngine(
            database=database,
            provider=provider,
            config=config,
        )

        rag_service = None

        if args.live_llm:
            llm = GroqProvider()

            rag_service = RAGService(
                retrieval=engine,
                llm=llm,
                model_name=llm.model,
                min_cosine=float(
                    os.getenv(
                        "WEBINTEL_RAG_MIN_COSINE",
                        "0.20",
                    )
                ),
            )

        retrieval_metrics = []
        first_query_ms = None
        warm_query_ms = None
        rag_latencies = []
        behavior_correct = []

        for case in dataset["cases"]:
            question = case["question"]
            mode = case["mode"]

            filters = SearchFilters(
                document_type="article",
            )

            results, retrieval_ms = await timed_search(
                engine,
                question,
                mode,
                args.k,
                filters,
            )

            if first_query_ms is None:
                first_query_ms = retrieval_ms

                # Same question, model and collection:
                # warm-process comparison.
                _, warm_query_ms = await timed_search(
                    engine,
                    question,
                    mode,
                    args.k,
                    filters,
                )

            # Convert chunk ranking to a unique
            # document ranking.
            ranked_documents = list(
                dict.fromkeys(
                    str(result["document_id"])
                    for result in results
                )
            )

            record = {
                "case_id": case["id"],
                "question": question,
                "expected_behavior": (
                    case["expected_behavior"]
                ),
                "retrieved_document_ids": (
                    ranked_documents
                ),
                "retrieval_ms": retrieval_ms,
            }

            if case["relevant_document_ids"]:
                metrics = evaluate_retrieval(
                    ranked_documents,
                    case["relevant_document_ids"],
                    k=args.k,
                )

                retrieval_metrics.append(metrics)

                record["retrieval_metrics"] = (
                    asdict(metrics)
                )

            else:
                record["retrieval_metrics"] = None

            if rag_service is not None:
                request = AskRequest(
                    question=question,
                    mode=mode,
                    top_k=min(args.k, 8),
                    document_type="article",
                )

                started = time.perf_counter()

                response = await rag_service.ask(request)

                rag_ms = milliseconds(started)
                rag_latencies.append(rag_ms)

                behavior_matches = (
                    response.status
                    == case["expected_behavior"]
                )

                behavior_correct.append(
                    behavior_matches
                )

                # Resolve source passages directly
                # from indexed MongoDB chunks.
                cited_ids = [
                    citation.chunk_id
                    for citation in response.citations
                ]

                source_records = await database[
                    "document_chunks"
                ].find({
                    "_id": {"$in": cited_ids},
                    "config_key": config.key,
                }).to_list(length=None)

                evidence_by_id = {
                    str(item["_id"]): item["text"]
                    for item in source_records
                }

                groundedness = evaluate_groundedness(
                    response,
                    evidence_by_id,
                )

                record["rag"] = {
                    "status": response.status,
                    "model": response.model,
                    "behavior_matches": (
                        behavior_matches
                    ),
                    "latency_ms": rag_ms,
                    "retrieved_chunks": (
                        response.retrieved_chunks
                    ),
                    "abstention_reason": (
                        response.abstention_reason
                    ),
                    "groundedness": (
                        asdict(groundedness)
                    ),
                    "strict_support_rate": (
                        groundedness.strict_support_rate
                    ),
                }

            report["cases"].append(record)

        report["retrieval_summary"] = (
            aggregate_metrics(retrieval_metrics)
            if retrieval_metrics
            else None
        )

        report["latency"] = {
            "model_load_ms": (
                report["model_load_ms"]
            ),
            "first_query_ms": first_query_ms,
            "warm_query_ms": warm_query_ms,
            "mean_retrieval_ms": round(
                mean(
                    item["retrieval_ms"]
                    for item in report["cases"]
                ),
                3,
            ) if report["cases"] else None,
            "mean_rag_ms": round(
                mean(rag_latencies), 3
            ) if rag_latencies else None,
        }

        report["behavior_accuracy"] = (
            mean(behavior_correct)
            if behavior_correct
            else None
        )

    finally:
        await client.close()

    destination = Path(args.output)
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(json.dumps({
        "dataset": report["dataset_id"],
        "cases": len(report["cases"]),
        "retrieval": report["retrieval_summary"],
        "behavior_accuracy": (
            report["behavior_accuracy"]
        ),
        "latency": report["latency"],
        "report_file": str(destination),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="WebIntel AI evaluation"
    )

    parser.add_argument(
        "--dataset",
        default="evaluation/cases.json",
    )
    parser.add_argument(
        "--output",
        default="evaluation/reports/latest.json",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--live-llm",
        action="store_true",
    )

    args = parser.parse_args()

    if not 1 <= args.k <= 8:
        parser.error("--k must be between 1 and 8")

    asyncio.run(evaluate(args))


if __name__ == "__main__":
    main()
