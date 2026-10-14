import type {
  DocumentChangeHistoryItem,
  DocumentListParams,
  DocumentListResponse,
  DocumentRevision,
  DocumentRevisionsResponse,
  DocumentSourcesResponse,
  DocumentTimeline,
  ExtractionMethod,
  RevisionChange,
  RevisionComparison,
  SourceObservation,
  WebDocument,
} from '../../types/documents'
import { apiRequest, invalidResponse } from './client'

type ObjectValue = Record<string, unknown>
const isObject = (value: unknown): value is ObjectValue =>
  typeof value === 'object' && value !== null && !Array.isArray(value)
const isString = (value: unknown): value is string => typeof value === 'string'
const isNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean'
const isNullableString = (value: unknown): value is string | null => value === null || isString(value)
const methods: ExtractionMethod[] = ['scrapy', 'playwright', 'httpx']

export function parseDocument(value: unknown): WebDocument {
  if (
    !isObject(value) ||
    value.schema_version !== '1.0' ||
    !isString(value.document_id) ||
    (value.document_type !== 'article' && value.document_type !== 'quote') ||
    !isString(value.title) ||
    !isString(value.content) ||
    !isString(value.source_url) ||
    !isString(value.source_domain) ||
    !isNullableString(value.author) ||
    !Array.isArray(value.tags) ||
    !value.tags.every(isString) ||
    !isNullableString(value.published_at) ||
    !isString(value.scraped_at) ||
    !methods.includes(value.extraction_method as ExtractionMethod) ||
    !isString(value.content_hash) ||
    !isObject(value.metadata)
  ) {
    invalidResponse('A document does not match the expected API contract.')
  }
  return value as unknown as WebDocument
}

export function parseDocumentList(value: unknown): DocumentListResponse {
  if (
    !isObject(value) ||
    !Array.isArray(value.items) ||
    !isNumber(value.total) ||
    !isNumber(value.page) ||
    !isNumber(value.page_size) ||
    !isNumber(value.total_pages) ||
    !isBoolean(value.has_next) ||
    !isBoolean(value.has_previous)
  ) {
    invalidResponse('The document list does not match the expected API contract.')
  }
  return {
    items: value.items.map(parseDocument),
    total: value.total,
    page: value.page,
    page_size: value.page_size,
    total_pages: value.total_pages,
    has_next: value.has_next,
    has_previous: value.has_previous,
  }
}

function parseObservation(value: unknown): SourceObservation {
  if (
    !isObject(value) ||
    !isString(value.observation_id) ||
    !isString(value.document_id) ||
    !isString(value.source_url) ||
    !methods.includes(value.extraction_method as ExtractionMethod) ||
    !isString(value.content_hash) ||
    !isString(value.first_seen_at) ||
    !isString(value.last_seen_at)
  ) {
    invalidResponse('A provenance record does not match the expected API contract.')
  }
  return value as unknown as SourceObservation
}

export function parseSources(value: unknown): DocumentSourcesResponse {
  if (!isObject(value) || !isString(value.document_id) || !isNumber(value.total) || !Array.isArray(value.items)) {
    invalidResponse('The provenance response does not match the expected API contract.')
  }
  return { document_id: value.document_id, total: value.total, items: value.items.map(parseObservation) }
}

function parseRevision(value: unknown): DocumentRevision {
  if (
    !isObject(value) ||
    !isString(value.revision_id) ||
    !isString(value.document_id) ||
    !isString(value.content_hash) ||
    !isString(value.title) ||
    !isString(value.content) ||
    !isString(value.observed_at)
  ) {
    invalidResponse('A revision does not match the expected API contract.')
  }
  return value as unknown as DocumentRevision
}

export function parseRevisions(value: unknown): DocumentRevisionsResponse {
  if (!isObject(value) || !isString(value.document_id) || !isNumber(value.total) || !Array.isArray(value.items)) {
    invalidResponse('The revision response does not match the expected API contract.')
  }
  return { document_id: value.document_id, total: value.total, items: value.items.map(parseRevision) }
}

function parseHistoryItem(value: unknown): DocumentChangeHistoryItem {
  if (
    !isObject(value) ||
    !isString(value.from_revision_id) ||
    !isString(value.to_revision_id) ||
    !isString(value.observed_at) ||
    !isBoolean(value.title_changed) ||
    !isBoolean(value.content_changed) ||
    !isNumber(value.added_words) ||
    !isNumber(value.removed_words) ||
    !isNumber(value.similarity_ratio) ||
    !isString(value.change_summary)
  ) {
    invalidResponse('A change-history item does not match the expected API contract.')
  }
  return value as unknown as DocumentChangeHistoryItem
}

export function parseTimeline(value: unknown): DocumentTimeline {
  if (
    !isObject(value) ||
    !isString(value.document_id) ||
    !isNumber(value.revision_count) ||
    !isNumber(value.change_count) ||
    !Array.isArray(value.history)
  ) {
    invalidResponse('The change timeline does not match the expected API contract.')
  }
  return {
    document_id: value.document_id,
    revision_count: value.revision_count,
    change_count: value.change_count,
    history: value.history.map(parseHistoryItem),
  }
}

function parseChange(value: unknown): RevisionChange {
  if (
    !isObject(value) ||
    !['replace', 'delete', 'insert'].includes(String(value.kind)) ||
    !isString(value.before_excerpt) ||
    !isString(value.after_excerpt) ||
    !isNumber(value.removed_words) ||
    !isNumber(value.added_words)
  ) {
    invalidResponse('A comparison excerpt does not match the expected API contract.')
  }
  return value as unknown as RevisionChange
}

export function parseComparison(value: unknown): RevisionComparison {
  if (!isObject(value) || !Array.isArray(value.changes)) {
    invalidResponse('The revision comparison does not match the expected API contract.')
  }
  const strings = [
    'document_id', 'from_revision_id', 'to_revision_id', 'from_observed_at', 'to_observed_at',
    'from_content_hash', 'to_content_hash', 'before_title', 'after_title', 'change_summary',
  ] as const
  const numbers = ['before_word_count', 'after_word_count', 'added_words', 'removed_words', 'similarity_ratio'] as const
  if (
    !strings.every((key) => isString(value[key])) ||
    !numbers.every((key) => isNumber(value[key])) ||
    !isBoolean(value.content_changed) ||
    !isBoolean(value.title_changed) ||
    !isBoolean(value.changes_truncated)
  ) {
    invalidResponse('The revision comparison does not match the expected API contract.')
  }
  return { ...(value as unknown as RevisionComparison), changes: value.changes.map(parseChange) }
}

function documentPath(documentId: string, suffix = ''): string {
  return `/api/v1/documents/${encodeURIComponent(documentId)}${suffix}`
}

export const documentsApi = {
  list: async (params: DocumentListParams, signal?: AbortSignal) => {
    const query = new URLSearchParams({ page: String(params.page), page_size: String(params.pageSize) })
    if (params.documentType) query.set('document_type', params.documentType)
    if (params.sourceDomain) query.set('source_domain', params.sourceDomain)
    if (params.tag) query.set('tag', params.tag)
    if (params.query) query.set('q', params.query)
    return parseDocumentList(await apiRequest(`/api/v1/documents?${query}`, { signal }))
  },
  detail: async (documentId: string, signal?: AbortSignal) =>
    parseDocument(await apiRequest(documentPath(documentId), { signal })),
  sources: async (documentId: string, signal?: AbortSignal) =>
    parseSources(await apiRequest(documentPath(documentId, '/sources'), { signal })),
  revisions: async (documentId: string, signal?: AbortSignal) =>
    parseRevisions(await apiRequest(documentPath(documentId, '/revisions'), { signal })),
  timeline: async (documentId: string, signal?: AbortSignal) =>
    parseTimeline(await apiRequest(`/api/v1/analytics/documents/${encodeURIComponent(documentId)}/changes`, { signal })),
  compare: async (documentId: string, fromRevisionId: string, toRevisionId: string, signal?: AbortSignal) => {
    const query = new URLSearchParams({ from_revision_id: fromRevisionId, to_revision_id: toRevisionId })
    return parseComparison(
      await apiRequest(`/api/v1/analytics/documents/${encodeURIComponent(documentId)}/compare?${query}`, { signal }),
    )
  },
}
