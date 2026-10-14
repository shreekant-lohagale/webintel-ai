import type {
  DashboardSummary,
  DomainIntelligence,
  DomainSummary,
  FreshnessCounts,
  ReadinessResponse,
  RevisionActivity,
  RevisionActivityPoint,
  TopicTerm,
} from '../../types/dashboard'
import { apiRequest, invalidResponse } from './client'

const statuses = [
  'recently_observed',
  'aging_observation',
  'stale_observation',
  'future_timestamp',
  'unknown',
] as const

type ObjectValue = Record<string, unknown>
const isObject = (value: unknown): value is ObjectValue =>
  typeof value === 'object' && value !== null && !Array.isArray(value)
const isString = (value: unknown): value is string => typeof value === 'string'
const isNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const isNullableString = (value: unknown): value is string | null => value === null || isString(value)

function parseFreshness(value: unknown): FreshnessCounts {
  if (!isObject(value) || !statuses.every((status) => isNumber(value[status]))) {
    invalidResponse('The freshness summary does not match the expected API contract.')
  }
  return Object.fromEntries(statuses.map((status) => [status, value[status]])) as FreshnessCounts
}

function parseTopic(value: unknown): TopicTerm {
  if (!isObject(value) || !isString(value.term) || !isNumber(value.document_frequency)) {
    invalidResponse('A topic row does not match the expected API contract.')
  }
  return { term: value.term, document_frequency: value.document_frequency }
}

export function parseDashboardSummary(value: unknown): DashboardSummary {
  if (!isObject(value) || !isObject(value.kpis) || !Array.isArray(value.top_topics)) {
    invalidResponse('The dashboard summary does not match the expected API contract.')
  }
  const kpis = value.kpis
  const numberKeys = [
    'document_count',
    'revision_count',
    'source_observation_count',
    'observed_document_count',
    'unobserved_document_count',
  ] as const
  if (
    !isString(value.as_of) ||
    !isNullableString(value.source_domain) ||
    !isString(value.counting_unit) ||
    !numberKeys.every((key) => isNumber(kpis[key])) ||
    !(kpis.coverage_ratio === null || isNumber(kpis.coverage_ratio)) ||
    !isObject(kpis.documents_by_type) ||
    !Object.values(kpis.documents_by_type).every(isNumber) ||
    !Array.isArray(value.limitations) ||
    !value.limitations.every(isString)
  ) {
    invalidResponse('The dashboard summary does not match the expected API contract.')
  }
  return {
    as_of: value.as_of,
    source_domain: value.source_domain,
    counting_unit: value.counting_unit,
    kpis: {
      document_count: kpis.document_count as number,
      revision_count: kpis.revision_count as number,
      source_observation_count: kpis.source_observation_count as number,
      observed_document_count: kpis.observed_document_count as number,
      unobserved_document_count: kpis.unobserved_document_count as number,
      coverage_ratio: kpis.coverage_ratio as number | null,
      documents_by_type: kpis.documents_by_type as Record<string, number>,
      freshness_status_counts: parseFreshness(kpis.freshness_status_counts),
    },
    top_topics: value.top_topics.map(parseTopic),
    limitations: value.limitations,
  }
}

function parseActivityPoint(value: unknown): RevisionActivityPoint {
  if (
    !isObject(value) ||
    !isString(value.date) ||
    !isNumber(value.revision_count) ||
    !isNumber(value.unique_document_count)
  ) {
    invalidResponse('A revision activity point does not match the expected API contract.')
  }
  return {
    date: value.date,
    revision_count: value.revision_count,
    unique_document_count: value.unique_document_count,
  }
}

export function parseRevisionActivity(value: unknown): RevisionActivity {
  if (
    !isObject(value) ||
    !isNullableString(value.source_domain) ||
    !isString(value.start) ||
    !isString(value.end) ||
    !isString(value.counting_unit) ||
    !isNumber(value.total_revisions) ||
    !Array.isArray(value.series) ||
    !isString(value.caution)
  ) {
    invalidResponse('Revision activity does not match the expected API contract.')
  }
  return {
    source_domain: value.source_domain,
    start: value.start,
    end: value.end,
    counting_unit: value.counting_unit,
    total_revisions: value.total_revisions,
    series: value.series.map(parseActivityPoint),
    caution: value.caution,
  }
}

function parseDomain(value: unknown): DomainIntelligence {
  if (
    !isObject(value) ||
    !isString(value.source_domain) ||
    !isNumber(value.document_count) ||
    !isNumber(value.observed_document_count) ||
    !isNumber(value.coverage_ratio) ||
    !isNullableString(value.latest_observed_at)
  ) {
    invalidResponse('A domain row does not match the expected API contract.')
  }
  return {
    source_domain: value.source_domain,
    document_count: value.document_count,
    observed_document_count: value.observed_document_count,
    coverage_ratio: value.coverage_ratio,
    latest_observed_at: value.latest_observed_at,
    status_counts: parseFreshness(value.status_counts),
  }
}

export function parseDomainSummary(value: unknown): DomainSummary {
  if (
    !isObject(value) ||
    !isString(value.as_of) ||
    !isString(value.counting_unit) ||
    !isNumber(value.total_domains) ||
    !Array.isArray(value.domains)
  ) {
    invalidResponse('The domain summary does not match the expected API contract.')
  }
  return {
    as_of: value.as_of,
    counting_unit: value.counting_unit,
    total_domains: value.total_domains,
    domains: value.domains.map(parseDomain),
  }
}

export function parseReadiness(value: unknown): ReadinessResponse {
  if (!isObject(value) || !isString(value.status) || !isString(value.database)) {
    invalidResponse('The readiness response does not match the expected API contract.')
  }
  return { status: value.status, database: value.database }
}

export const dashboardApi = {
  summary: async (signal?: AbortSignal) =>
    parseDashboardSummary(await apiRequest('/api/v1/analytics/dashboard/summary', { signal })),
  domains: async (signal?: AbortSignal) =>
    parseDomainSummary(await apiRequest('/api/v1/analytics/dashboard/domains', { signal })),
  revisionActivity: async (start: string, end: string, signal?: AbortSignal) => {
    const params = new URLSearchParams({ start, end })
    return parseRevisionActivity(
      await apiRequest(`/api/v1/analytics/dashboard/revision-activity?${params.toString()}`, { signal }),
    )
  },
  readiness: async (signal?: AbortSignal) =>
    parseReadiness(await apiRequest('/api/v1/health/ready', { signal, timeoutMs: 5_000 })),
}
