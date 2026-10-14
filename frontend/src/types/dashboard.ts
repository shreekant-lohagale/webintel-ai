export type FreshnessStatus =
  | 'recently_observed'
  | 'aging_observation'
  | 'stale_observation'
  | 'future_timestamp'
  | 'unknown'

export type FreshnessCounts = Record<FreshnessStatus, number>

export interface TopicTerm {
  term: string
  document_frequency: number
}

export interface DashboardKpis {
  document_count: number
  revision_count: number
  source_observation_count: number
  observed_document_count: number
  unobserved_document_count: number
  coverage_ratio: number | null
  documents_by_type: Record<string, number>
  freshness_status_counts: FreshnessCounts
}

export interface DashboardSummary {
  as_of: string
  source_domain: string | null
  counting_unit: string
  kpis: DashboardKpis
  top_topics: TopicTerm[]
  limitations: string[]
}

export interface RevisionActivityPoint {
  date: string
  revision_count: number
  unique_document_count: number
}

export interface RevisionActivity {
  source_domain: string | null
  start: string
  end: string
  counting_unit: string
  total_revisions: number
  series: RevisionActivityPoint[]
  caution: string
}

export interface DomainIntelligence {
  source_domain: string
  document_count: number
  observed_document_count: number
  coverage_ratio: number
  latest_observed_at: string | null
  status_counts: FreshnessCounts
}

export interface DomainSummary {
  as_of: string
  counting_unit: string
  total_domains: number
  domains: DomainIntelligence[]
}

export interface ReadinessResponse {
  status: string
  database: string
}
