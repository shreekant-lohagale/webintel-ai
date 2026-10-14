
from app.evaluation.groundedness import (
    claim_entailment,
    evaluate_groundedness,
)
from app.rag.schemas import (
    AnswerCitation,
    AnswerClaim,
    AskResponse,
)


SOURCE = (
    "Reliable data pipelines combine extraction, "
    "validation, provenance, and durable storage."
)


def make_response(
    claim_text=SOURCE,
    quote=SOURCE,
    chunk_id="chunk1",
):
    citation = AnswerCitation(
        evidence_id="E1",
        document_id="doc1",
        chunk_id=chunk_id,
        title="Data Pipelines",
        source_url="https://example.com/data",
        quote=quote,
    )

    return AskResponse(
        question="What do pipelines combine?",
        status="answered",
        answer=claim_text + " [E1]",
        claims=[
            AnswerClaim(
                text=claim_text,
                citations=[citation],
            )
        ],
        citations=[citation],
        retrieved_chunks=1,
        model="fake-model",
    )


def test_exact_text_supported():
    assert claim_entailment(
        SOURCE,
        SOURCE,
    ) == "supported"


def test_whitespace_differences_supported():
    assert claim_entailment(
        "Reliable  data pipelines",
        SOURCE,
    ) == "supported"


def test_paraphrase_is_not_auto_approved():
    assert claim_entailment(
        "Good pipelines keep data reliable.",
        SOURCE,
    ) == "unverified"


def test_different_numbers_flagged():
    assert claim_entailment(
        "Revenue was 300 million",
        "Revenue was 200 million",
    ) == "contradicted"


def test_valid_citation_grounded():
    response = make_response()

    report = evaluate_groundedness(
        response,
        {"chunk1": SOURCE},
    )

    assert report.total_claims == 1
    assert report.supported == 1
    assert report.invalid_citations == 0
    assert report.strict_support_rate == 1.0


def test_fabricated_source_quote_detected():
    response = make_response(
        quote="This quote is not in the source."
    )

    report = evaluate_groundedness(
        response,
        {"chunk1": SOURCE},
    )

    assert report.invalid_citations == 1
    assert report.unverified == 1


def test_missing_chunk_detected():
    response = make_response(
        chunk_id="invented-chunk"
    )

    report = evaluate_groundedness(
        response,
        {"chunk1": SOURCE},
    )

    assert report.invalid_citations == 1


def test_abstention_has_no_support_rate():
    response = AskResponse(
        question="Unrelated question",
        status="abstained",
        answer="Insufficient evidence",
        claims=[],
        citations=[],
        retrieved_chunks=0,
        model="fake-model",
    )

    report = evaluate_groundedness(
        response, {}
    )

    assert report.total_claims == 0
    assert report.strict_support_rate is None
