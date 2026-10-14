
import re
from dataclasses import dataclass
from typing import Literal

from app.rag.schemas import AskResponse


EntailmentStatus = Literal[
    "supported",
    "contradicted",
    "unverified",
]


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def numbers(text: str) -> set[str]:
    return set(re.findall(
        r"\b\d+(?:[.,]\d+)*%?\b",
        text,
    ))


def claim_entailment(
    claim: str,
    evidence: str,
) -> EntailmentStatus:
    """
    Conservative lexical entailment checker.

    'supported' is reserved for a claim that occurs
    verbatim in evidence (ignoring case/whitespace).

    Different explicit numeric values are flagged as
    potential contradictions, not proof of contradiction.

    Everything else remains unverified.
    """
    claim_text = normalize(claim)
    evidence_text = normalize(evidence)

    if not claim_text or not evidence_text:
        return "unverified"

    if claim_text in evidence_text:
        return "supported"

    claim_numbers = numbers(claim_text)
    evidence_numbers = numbers(evidence_text)

    if (
        claim_numbers
        and evidence_numbers
        and not claim_numbers.issubset(evidence_numbers)
    ):
        return "contradicted"

    return "unverified"


@dataclass(frozen=True)
class GroundednessReport:
    total_claims: int
    supported: int
    contradicted: int
    unverified: int
    invalid_citations: int

    @property
    def strict_support_rate(self) -> float | None:
        if self.total_claims == 0:
            return None

        return self.supported / self.total_claims


def evaluate_groundedness(
    response: AskResponse,
    evidence_by_chunk_id: dict[str, str],
) -> GroundednessReport:
    supported = 0
    contradicted = 0
    unverified = 0
    invalid = 0

    for claim in response.claims:
        statuses = []

        for citation in claim.citations:
            source_text = evidence_by_chunk_id.get(
                citation.chunk_id
            )

            if (
                source_text is None
                or normalize(citation.quote)
                not in normalize(source_text)
            ):
                invalid += 1
                statuses.append("unverified")
                continue

            statuses.append(
                claim_entailment(
                    claim.text,
                    citation.quote,
                )
            )

        if not statuses:
            unverified += 1
        elif "contradicted" in statuses:
            contradicted += 1
        elif "supported" in statuses:
            supported += 1
        else:
            unverified += 1

    return GroundednessReport(
        total_claims=len(response.claims),
        supported=supported,
        contradicted=contradicted,
        unverified=unverified,
        invalid_citations=invalid,
    )
