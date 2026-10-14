export type DocumentType = 'article' | 'quote'
export type ExtractionMethod = 'scrapy' | 'playwright' | 'httpx'

export interface WebDocument {
  schema_version: '1.0'
  document_id: string
  document_type: DocumentType
  title: string
  content: string
  source_url: string
  source_domain: string
  author: string | null
  tags: string[]
  published_at: string | null
  scraped_at: string
  extraction_method: ExtractionMethod
  content_hash: string
  metadata: Record<string, unknown>
}

export interface DocumentListParams {
  page: number
  pageSize: number
  documentType?: DocumentType
  sourceDomain?: string
  tag?: string
  query?: string
}

export interface DocumentListResponse {
  items: WebDocument[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface SourceObservation {
  observation_id: string
  document_id: string
  source_url: string
  extraction_method: ExtractionMethod
  content_hash: string
  first_seen_at: string
  last_seen_at: string
}

export interface DocumentSourcesResponse {
  document_id: string
  total: number
  items: SourceObservation[]
}

export interface DocumentRevision {
  revision_id: string
  document_id: string
  content_hash: string
  title: string
  content: string
  observed_at: string
}

export interface DocumentRevisionsResponse {
  document_id: string
  total: number
  items: DocumentRevision[]
}

export interface DocumentChangeHistoryItem {
  from_revision_id: string
  to_revision_id: string
  observed_at: string
  title_changed: boolean
  content_changed: boolean
  added_words: number
  removed_words: number
  similarity_ratio: number
  change_summary: string
}

export interface DocumentTimeline {
  document_id: string
  revision_count: number
  change_count: number
  history: DocumentChangeHistoryItem[]
}

export type RevisionChangeKind = 'replace' | 'delete' | 'insert'

export interface RevisionChange {
  kind: RevisionChangeKind
  before_excerpt: string
  after_excerpt: string
  removed_words: number
  added_words: number
}

export interface RevisionComparison {
  document_id: string
  from_revision_id: string
  to_revision_id: string
  from_observed_at: string
  to_observed_at: string
  from_content_hash: string
  to_content_hash: string
  content_changed: boolean
  title_changed: boolean
  before_title: string
  after_title: string
  before_word_count: number
  after_word_count: number
  added_words: number
  removed_words: number
  similarity_ratio: number
  change_summary: string
  changes: RevisionChange[]
  changes_truncated: boolean
}
