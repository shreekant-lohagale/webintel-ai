from datetime import datetime, timezone
import pytest
from app.intelligence.topics import keywords, terms, term_frequencies, latest_per_document, compare_windows


def t(day, hour=0):
    return datetime(2026, 10, day, hour, tzinfo=timezone.utc)


def rev(doc, rev_id, text, when):
    return {'document_id': doc, 'revision_id': rev_id, 'content': text, 'observed_at': when}


def test_keywords_stopwords_and_punctuation():
    assert keywords('The AI pipeline, pipeline! is reliable.') == ['pipeline', 'pipeline', 'reliable']


def test_bigrams():
    assert 'data pipeline' in terms('The data pipeline succeeds', ngrams=2)


def test_document_frequency_deduplicates():
    result = term_frequencies([{'content': 'pipeline pipeline AI'}, {'content': 'pipeline works'}])
    assert result[0] == {'term': 'pipeline', 'document_frequency': 2}


def test_deterministic_tie_order():
    assert [x['term'] for x in term_frequencies([{'content': 'zebra apple'}])] == ['apple', 'zebra']


def test_latest_revision_per_document():
    rows = latest_per_document([rev('a', '1', 'old', t(1)), rev('a', '2', 'new', t(2))])
    assert len(rows) == 1 and rows[0]['content'] == 'new'


def test_trend_increases_and_decreases():
    before = [rev('a', '1', 'python python', t(1)), rev('b', '1', 'python', t(1))]
    after = [rev('a', '2', 'cloud', t(3)), rev('b', '2', 'python cloud', t(3))]
    terms = {x['term']: x for x in compare_windows(before, after)['terms']}
    assert terms['python']['delta'] == -1
    assert terms['cloud']['delta'] == 2 and terms['cloud']['status'] == 'emerging'


def test_repeat_revision_not_double_counted():
    before = [rev('a', '1', 'python', t(1)), rev('a', '2', 'python cloud', t(2))]
    rows = compare_windows(before, [])
    assert rows['before_document_count'] == 1
    assert next(v for v in rows['terms'] if v['term'] == 'python')['before_df'] == 1


def test_empty_data():
    assert compare_windows([], [])['terms'] == []


def test_invalid_ngram():
    with pytest.raises(ValueError):
        terms('example', ngrams=3)
