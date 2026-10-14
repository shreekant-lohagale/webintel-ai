"""Deterministic lexical topics and document-frequency trend calculations."""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

STOPWORDS = frozenset('''a about above after again all also am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not now of off on once only or other our ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they this those through to too under until up very was we were what when where which while who whom why will with you your yours yourself yourselves using use used report reports updated update new old said says also'''.split())
WORD_RE = re.compile(r"(?u)\b[^\W\d_][\w'-]*\b")


def keywords(text: str, *, min_length: int = 3) -> list[str]:
    """Lower-case word tokens with stopword removal, no network or ML calls."""
    words = [s.lower().strip("'-") for s in WORD_RE.findall(text or '')]
    return [w for w in words if len(w) >= min_length and w not in STOPWORDS and not w.isdigit()]


def terms(text: str, *, ngrams: int = 1) -> set[str]:
    """Presence set: each term counted at most once per source document."""
    words = keywords(text)
    values = set(words)
    if ngrams == 2:
        values.update(f'{a} {b}' for a, b in zip(words, words[1:]))
    elif ngrams != 1:
        raise ValueError('ngrams must be 1 or 2')
    return values


def term_frequencies(documents: list[dict], *, top_k: int = 20, ngrams: int = 1) -> list[dict]:
    if not 1 <= top_k <= 100:
        raise ValueError('top_k must be 1..100')
    counts: Counter[str] = Counter()
    for doc in documents:
        counts.update(terms(doc.get('content', ''), ngrams=ngrams))
    return [
        {'term': term, 'document_frequency': count}
        for term, count in sorted(counts.items(), key=lambda p: (-p[1], p[0]))[:top_k]
    ]


def normalize_time(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def latest_per_document(revisions: list[dict]) -> list[dict]:
    """One snapshot per logical document, sorted deterministically."""
    latest: dict[str, dict] = {}
    for rev in revisions:
        doc_id = str(rev['document_id'])
        ordering = (normalize_time(rev['observed_at']), str(rev.get('revision_id', '')))
        prev = latest.get(doc_id)
        if prev is None or ordering > (
            normalize_time(prev['observed_at']), str(prev.get('revision_id', ''))
        ):
            latest[doc_id] = rev
    return [latest[k] for k in sorted(latest)]


def compare_windows(
    before: list[dict], after: list[dict], *, top_k: int = 20, ngrams: int = 1
) -> dict:
    """Compare DF on one latest revision per document in each separate window."""
    if not 1 <= top_k <= 100:
        raise ValueError("top_k must be 1..100")
    if ngrams not in (1, 2):
        raise ValueError("ngrams must be 1 or 2")
    before_docs = latest_per_document(before)
    after_docs = latest_per_document(after)
    def df(docs: list[dict]) -> Counter[str]:
        counter: Counter[str] = Counter()
        for d in docs:
            counter.update(terms(d.get('content', ''), ngrams=ngrams))
        return counter
    previous, current = df(before_docs), df(after_docs)
    rows = []
    for term in previous.keys() | current.keys():
        old, new = previous[term], current[term]
        delta = new - old
        rows.append({
            'term': term, 'before_df': old, 'after_df': new, 'delta': delta,
            'status': 'emerging' if old == 0 else 'disappeared' if new == 0 else 'rising' if delta > 0 else 'falling' if delta < 0 else 'stable',
        })
    rows.sort(key=lambda x: (-abs(x['delta']), -x['after_df'], x['term']))
    return {
        'before_document_count': len(before_docs),
        'after_document_count': len(after_docs),
        'terms': rows[:top_k],
        'total_distinct_terms': len(rows),
    }
