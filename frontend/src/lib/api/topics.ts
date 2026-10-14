import type { DomainTopicsReport, TopicQuery, TopicReport, TopicTrendQuery, TopicTrendsReport } from '../../types/topics'
import { apiRequest, invalidResponse } from './client'

type ObjectValue = Record<string, unknown>
const isObject = (value: unknown): value is ObjectValue => typeof value === 'object' && value !== null && !Array.isArray(value)
const isString = (value: unknown): value is string => typeof value === 'string'
const isNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const isNullableString = (value: unknown): value is string | null => value === null || isString(value)
const trendStatuses = ['emerging', 'disappeared', 'rising', 'falling', 'stable'] as const

function parseTerm(value: unknown) {
  if (!isObject(value) || !isString(value.term) || !isNumber(value.document_frequency)) invalidResponse('A topic term does not match the expected API contract.')
  return { term: value.term, document_frequency: value.document_frequency }
}

export function parseTopicReport(value: unknown): TopicReport {
  if (!isObject(value) || !isNullableString(value.source_domain) || !isNumber(value.document_count) || !isString(value.counting_unit) || !Array.isArray(value.terms)) invalidResponse('The topic report does not match the expected API contract.')
  return { source_domain: value.source_domain, document_count: value.document_count, counting_unit: value.counting_unit, terms: value.terms.map(parseTerm) }
}

export function parseDomainTopics(value: unknown): DomainTopicsReport {
  if (!isObject(value) || !isNumber(value.document_count) || !isString(value.counting_unit) || !Array.isArray(value.domains)) invalidResponse('The domain topic report does not match the expected API contract.')
  return { document_count: value.document_count, counting_unit: value.counting_unit, domains: value.domains.map((domain) => {
    if (!isObject(domain) || !isString(domain.source_domain) || !isNumber(domain.document_count) || !Array.isArray(domain.terms)) invalidResponse('A domain topic row does not match the expected API contract.')
    return { source_domain: domain.source_domain, document_count: domain.document_count, terms: domain.terms.map(parseTerm) }
  }) }
}

export function parseTopicTrends(value: unknown): TopicTrendsReport {
  if (!isObject(value) || !isNullableString(value.source_domain) || !isString(value.counting_unit) || !isString(value.before_start) || !isString(value.before_end) || !isString(value.after_start) || !isString(value.after_end) || !isNumber(value.before_document_count) || !isNumber(value.after_document_count) || !Array.isArray(value.terms) || !isNumber(value.total_distinct_terms) || !isString(value.caution)) invalidResponse('The topic trend report does not match the expected API contract.')
  const terms = value.terms.map((term) => {
    if (!isObject(term) || !isString(term.term) || !isNumber(term.before_df) || !isNumber(term.after_df) || !isNumber(term.delta) || !trendStatuses.includes(term.status as typeof trendStatuses[number])) invalidResponse('A topic trend row does not match the expected API contract.')
    return { term: term.term, before_df: term.before_df, after_df: term.after_df, delta: term.delta, status: term.status as typeof trendStatuses[number] }
  })
  return { source_domain: value.source_domain, counting_unit: value.counting_unit, before_start: value.before_start, before_end: value.before_end, after_start: value.after_start, after_end: value.after_end, before_document_count: value.before_document_count, after_document_count: value.after_document_count, terms, total_distinct_terms: value.total_distinct_terms, caution: value.caution }
}

function commonParams(query: TopicQuery) {
  const params = new URLSearchParams({ limit: String(query.limit), ngrams: String(query.ngrams) })
  if (query.sourceDomain) params.set('source_domain', query.sourceDomain)
  if (query.maxDocuments) params.set('max_documents', String(query.maxDocuments))
  return params
}

export const topicsApi = {
  topics: async (query: TopicQuery, signal?: AbortSignal) => parseTopicReport(await apiRequest(`/api/v1/analytics/topics?${commonParams(query)}`, { signal })),
  domains: async (limit: number, topK: number, ngrams: 1 | 2, signal?: AbortSignal) => {
    const params = new URLSearchParams({ limit: String(limit), top_k: String(topK), ngrams: String(ngrams) })
    return parseDomainTopics(await apiRequest(`/api/v1/analytics/topics/domains?${params}`, { signal }))
  },
  trends: async (query: TopicTrendQuery, signal?: AbortSignal) => {
    const params = commonParams(query)
    params.set('before_start', query.beforeStart); params.set('before_end', query.beforeEnd)
    params.set('after_start', query.afterStart); params.set('after_end', query.afterEnd)
    return parseTopicTrends(await apiRequest(`/api/v1/analytics/topics/trends?${params}`, { signal }))
  },
}
