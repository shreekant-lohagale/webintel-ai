import type {
  DocumentListResponse,
  DocumentRevisionsResponse,
  DocumentSourcesResponse,
  DocumentTimeline,
  RevisionComparison,
  WebDocument,
} from '../types/documents'

export const documentId = 'a'.repeat(64)
export const olderRevisionId = '1'.repeat(64)
export const newerRevisionId = '2'.repeat(64)

export const documentFixture: WebDocument = {
  schema_version: '1.0',
  document_id: documentId,
  document_type: 'article',
  title: 'Reliable Intelligence Pipelines',
  content: 'Reliable public web intelligence requires provenance and careful validation.',
  source_url: 'https://example.com/intelligence',
  source_domain: 'example.com',
  author: 'Research Desk',
  tags: ['intelligence', 'validation'],
  published_at: '2026-10-10T08:00:00Z',
  scraped_at: '2026-10-14T09:30:00Z',
  extraction_method: 'scrapy',
  content_hash: 'b'.repeat(64),
  metadata: { language: 'en' },
}

export const documentListFixture: DocumentListResponse = {
  items: [documentFixture],
  total: 21,
  page: 1,
  page_size: 20,
  total_pages: 2,
  has_next: true,
  has_previous: false,
}

export const revisionsFixture: DocumentRevisionsResponse = {
  document_id: documentId,
  total: 2,
  items: [
    { revision_id: newerRevisionId, document_id: documentId, content_hash: 'b'.repeat(64), title: documentFixture.title, content: documentFixture.content, observed_at: '2026-10-14T09:30:00Z' },
    { revision_id: olderRevisionId, document_id: documentId, content_hash: 'c'.repeat(64), title: 'Intelligence Pipelines', content: 'Public web intelligence requires provenance.', observed_at: '2026-10-12T09:30:00Z' },
  ],
}

export const sourcesFixture: DocumentSourcesResponse = {
  document_id: documentId,
  total: 1,
  items: [{
    observation_id: 'd'.repeat(64),
    document_id: documentId,
    source_url: documentFixture.source_url,
    extraction_method: 'scrapy',
    content_hash: documentFixture.content_hash,
    first_seen_at: '2026-10-12T09:30:00Z',
    last_seen_at: '2026-10-14T09:30:00Z',
  }],
}

export const timelineFixture: DocumentTimeline = {
  document_id: documentId,
  revision_count: 2,
  change_count: 1,
  history: [{
    from_revision_id: olderRevisionId,
    to_revision_id: newerRevisionId,
    observed_at: '2026-10-14T09:30:00Z',
    title_changed: true,
    content_changed: true,
    added_words: 5,
    removed_words: 1,
    similarity_ratio: 0.72,
    change_summary: 'Content changed: 5 words added and 1 words removed. Title also changed.',
  }],
}

export const comparisonFixture: RevisionComparison = {
  document_id: documentId,
  from_revision_id: olderRevisionId,
  to_revision_id: newerRevisionId,
  from_observed_at: '2026-10-12T09:30:00Z',
  to_observed_at: '2026-10-14T09:30:00Z',
  from_content_hash: 'c'.repeat(64),
  to_content_hash: 'b'.repeat(64),
  content_changed: true,
  title_changed: true,
  before_title: 'Intelligence Pipelines',
  after_title: documentFixture.title,
  before_word_count: 5,
  after_word_count: 10,
  added_words: 5,
  removed_words: 1,
  similarity_ratio: 0.72,
  change_summary: 'Content changed: 5 words added and 1 words removed. Title also changed.',
  changes: [{ kind: 'replace', before_excerpt: 'Public web', after_excerpt: 'Reliable public web', removed_words: 1, added_words: 2 }],
  changes_truncated: false,
}
