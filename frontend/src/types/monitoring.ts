import type { FreshnessCounts, FreshnessStatus } from './dashboard'

export type { FreshnessStatus }

export interface MonitoringControls {
  sourceDomain?: string
  status?: FreshnessStatus
  asOf?: string
  freshHours: number
  staleHours: number
  maxDocuments?: number
  limit?: number
}

export interface MonitoringOverview {
  as_of: string
  source_domain: string | null
  counting_unit: string
  document_count: number
  observed_document_count: number
  unobserved_document_count: number
  coverage_ratio: number | null
  status_counts: FreshnessCounts
  fresh_hours: number
  stale_hours: number
  caution: string
}

export interface MonitoredDocument {
  document_id: string
  title: string | null
  source_domain: string
  document_type: string | null
  status: FreshnessStatus
  age_hours: number | null
  last_seen_at: string | null
  first_seen_at: string | null
  provenance_record_count: number
  distinct_source_url_count: number
  extraction_methods: string[]
  revision_count: number
}

export interface MonitoringDocuments {
  as_of: string
  total_matching: number
  limit: number
  items: MonitoredDocument[]
}

export interface MonitoringDomain {
  source_domain: string
  document_count: number
  observed_document_count: number
  coverage_ratio: number
  latest_observed_at: string | null
  status_counts: FreshnessCounts
}

export interface MonitoringDomains {
  as_of: string
  counting_unit: string
  domains: MonitoringDomain[]
}
