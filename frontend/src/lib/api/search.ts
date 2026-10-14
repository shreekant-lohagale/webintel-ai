import type { SearchHit, SearchMode, SearchRequest, SearchResponse, SourceCitation } from '../../types/search'
import { apiRequest, invalidResponse } from './client'

type ObjectValue = Record<string, unknown>
const isObject = (value: unknown): value is ObjectValue => typeof value === 'object' && value !== null && !Array.isArray(value)
const isString = (value: unknown): value is string => typeof value === 'string'
const isNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const isNullableNumber = (value: unknown): value is number | null => value === null || isNumber(value)
const modes: SearchMode[] = ['keyword', 'semantic', 'hybrid']

function isHttpUrl(value: unknown): value is string {
  if (!isString(value)) return false
  try {
    const protocol = new URL(value).protocol
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}

function parseCitation(value: unknown): SourceCitation {
  if (
    !isObject(value) ||
    !isString(value.document_id) ||
    !isString(value.chunk_id) ||
    !isHttpUrl(value.source_url) ||
    !isString(value.title)
  ) invalidResponse('A search citation does not match the expected API contract.')
  return value as unknown as SourceCitation
}

function parseHit(value: unknown): SearchHit {
  const strings = ['chunk_id', 'document_id', 'title', 'text', 'source_domain', 'document_type', 'content_hash', 'config_key'] as const
  if (
    !isObject(value) ||
    !isNumber(value.rank) ||
    !isNumber(value.chunk_index) ||
    !strings.every((key) => isString(value[key])) ||
    !isHttpUrl(value.source_url) ||
    !isNullableNumber(value.semantic_score) ||
    !isNullableNumber(value.bm25_score) ||
    !isNullableNumber(value.hybrid_score)
  ) invalidResponse('A search result does not match the expected API contract.')
  return { ...(value as unknown as SearchHit), citation: parseCitation(value.citation) }
}

export function parseSearchResponse(value: unknown): SearchResponse {
  if (
    !isObject(value) ||
    !isString(value.query) ||
    !modes.includes(value.mode as SearchMode) ||
    !isNumber(value.count) ||
    !Array.isArray(value.results)
  ) invalidResponse('The search response does not match the expected API contract.')
  const results = value.results.map(parseHit)
  if (value.count !== results.length) invalidResponse('The search result count does not match the returned results.')
  return { query: value.query, mode: value.mode as SearchMode, count: value.count, results }
}

export const searchApi = {
  search: async (request: SearchRequest, signal?: AbortSignal) =>
    parseSearchResponse(await apiRequest('/api/v1/search', {
      method: 'POST',
      body: request,
      signal,
      timeoutMs: 30_000,
    })),
}
