import type { MonitoringControls, MonitoringDocuments, MonitoringDomains, MonitoringOverview, MonitoredDocument } from '../../types/monitoring'
import type { FreshnessCounts, FreshnessStatus } from '../../types/dashboard'
import { apiRequest, invalidResponse } from './client'

type ObjectValue = Record<string, unknown>
const isObject = (value: unknown): value is ObjectValue => typeof value === 'object' && value !== null && !Array.isArray(value)
const isString = (value: unknown): value is string => typeof value === 'string'
const isNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const isNullableString = (value: unknown): value is string | null => value === null || isString(value)
const statuses: FreshnessStatus[] = ['recently_observed', 'aging_observation', 'stale_observation', 'future_timestamp', 'unknown']

function parseCounts(value: unknown): FreshnessCounts {
  if (!isObject(value) || !statuses.every((status) => isNumber(value[status]))) invalidResponse('Freshness counts do not match the expected API contract.')
  return Object.fromEntries(statuses.map((status) => [status, value[status]])) as FreshnessCounts
}

export function parseMonitoringOverview(value: unknown): MonitoringOverview {
  if (!isObject(value) || !isString(value.as_of) || !isNullableString(value.source_domain) || !isString(value.counting_unit) || !isNumber(value.document_count) || !isNumber(value.observed_document_count) || !isNumber(value.unobserved_document_count) || !(value.coverage_ratio === null || isNumber(value.coverage_ratio)) || !isNumber(value.fresh_hours) || !isNumber(value.stale_hours) || !isString(value.caution)) invalidResponse('The monitoring overview does not match the expected API contract.')
  return { as_of: value.as_of, source_domain: value.source_domain, counting_unit: value.counting_unit, document_count: value.document_count, observed_document_count: value.observed_document_count, unobserved_document_count: value.unobserved_document_count, coverage_ratio: value.coverage_ratio, status_counts: parseCounts(value.status_counts), fresh_hours: value.fresh_hours, stale_hours: value.stale_hours, caution: value.caution }
}

function parseDocument(value: unknown): MonitoredDocument {
  if (!isObject(value) || !isString(value.document_id) || !isNullableString(value.title) || !isString(value.source_domain) || !isNullableString(value.document_type) || !statuses.includes(value.status as FreshnessStatus) || !(value.age_hours === null || isNumber(value.age_hours)) || !isNullableString(value.last_seen_at) || !isNullableString(value.first_seen_at) || !isNumber(value.provenance_record_count) || !isNumber(value.distinct_source_url_count) || !Array.isArray(value.extraction_methods) || !value.extraction_methods.every(isString) || !isNumber(value.revision_count)) invalidResponse('A monitored document does not match the expected API contract.')
  return value as unknown as MonitoredDocument
}

export function parseMonitoringDocuments(value: unknown): MonitoringDocuments {
  if (!isObject(value) || !isString(value.as_of) || !isNumber(value.total_matching) || !isNumber(value.limit) || !Array.isArray(value.items)) invalidResponse('The monitoring document report does not match the expected API contract.')
  return { as_of: value.as_of, total_matching: value.total_matching, limit: value.limit, items: value.items.map(parseDocument) }
}

export function parseMonitoringDomains(value: unknown): MonitoringDomains {
  if (!isObject(value) || !isString(value.as_of) || !isString(value.counting_unit) || !Array.isArray(value.domains)) invalidResponse('The monitoring domain report does not match the expected API contract.')
  return { as_of: value.as_of, counting_unit: value.counting_unit, domains: value.domains.map((domain) => {
    if (!isObject(domain) || !isString(domain.source_domain) || !isNumber(domain.document_count) || !isNumber(domain.observed_document_count) || !isNumber(domain.coverage_ratio) || !isNullableString(domain.latest_observed_at)) invalidResponse('A monitoring domain row does not match the expected API contract.')
    return { source_domain: domain.source_domain, document_count: domain.document_count, observed_document_count: domain.observed_document_count, coverage_ratio: domain.coverage_ratio, latest_observed_at: domain.latest_observed_at, status_counts: parseCounts(domain.status_counts) }
  }) }
}

function paramsFor(controls: MonitoringControls, endpoint: 'overview' | 'documents' | 'domains') {
  const params = new URLSearchParams({ fresh_hours: String(controls.freshHours), stale_hours: String(controls.staleHours) })
  if (endpoint !== 'domains' && controls.sourceDomain) params.set('source_domain', controls.sourceDomain)
  if (endpoint === 'documents' && controls.status) params.set('status', controls.status)
  if (controls.asOf) params.set('as_of', controls.asOf)
  if (controls.maxDocuments) params.set('max_documents', String(controls.maxDocuments))
  if (endpoint === 'documents' && controls.limit) params.set('limit', String(controls.limit))
  return params
}

export const monitoringApi = {
  overview: async (controls: MonitoringControls, signal?: AbortSignal) => parseMonitoringOverview(await apiRequest(`/api/v1/analytics/monitoring/overview?${paramsFor(controls, 'overview')}`, { signal })),
  documents: async (controls: MonitoringControls, signal?: AbortSignal) => parseMonitoringDocuments(await apiRequest(`/api/v1/analytics/monitoring/documents?${paramsFor(controls, 'documents')}`, { signal })),
  domains: async (controls: MonitoringControls, signal?: AbortSignal) => parseMonitoringDomains(await apiRequest(`/api/v1/analytics/monitoring/domains?${paramsFor(controls, 'domains')}`, { signal })),
}
