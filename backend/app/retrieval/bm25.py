
import math
import re
from collections import Counter
from typing import Sequence


TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.casefold())


class BM25:
    def __init__(
        self,
        texts: Sequence[str],
        k1: float = 1.5,
        b: float = 0.75,
    ):
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("Invalid BM25 parameters")

        self.k1 = k1
        self.b = b
        self.counts = [
            Counter(tokenize(text))
            for text in texts
        ]
        self.lengths = [
            sum(counts.values())
            for counts in self.counts
        ]

        self.size = len(self.counts)
        self.avg_length = (
            sum(self.lengths) / self.size
            if self.size else 0.0
        )

        document_frequency = Counter()

        for counts in self.counts:
            document_frequency.update(counts.keys())

        self.idf = {
            term: math.log(
                1 + (
                    self.size - frequency + 0.5
                ) / (frequency + 0.5)
            )
            for term, frequency
            in document_frequency.items()
        }

    def scores(self, query: str) -> list[float]:
        terms = set(tokenize(query))
        output = []

        for counts, length in zip(
            self.counts,
            self.lengths,
        ):
            score = 0.0

            for term in terms:
                frequency = counts.get(term, 0)

                if frequency == 0:
                    continue

                denominator = (
                    frequency
                    + self.k1
                    * (
                        1 - self.b
                        + self.b
                        * length
                        / max(self.avg_length, 1e-12)
                    )
                )

                score += self.idf[term] * (
                    frequency * (self.k1 + 1)
                    / denominator
                )

            output.append(score)

        return output
