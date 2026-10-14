import type { DashboardSummary, DomainSummary, RevisionActivity } from '../types/dashboard'

export const emptySummary: DashboardSummary = {
  as_of: '2026-10-14T12:00:00+00:00',
  source_domain: null,
  counting_unit: 'current_documents_bounded',
  kpis: {
    document_count: 0,
    revision_count: 0,
    source_observation_count: 0,
    observed_document_count: 0,
    unobserved_document_count: 0,
    coverage_ratio: null,
    documents_by_type: {},
    freshness_status_counts: {
      recently_observed: 0,
      aging_observation: 0,
      stale_observation: 0,
      future_timestamp: 0,
      unknown: 0,
    },
  },
  top_topics: [],
  limitations: [
    'Current-document sample is bounded.',
    'Observation age is not verified content freshness.',
    'Topics are deterministic keyword frequencies, not semantic classifications.',
  ],
}

export const populatedSummary: DashboardSummary = {
  ...emptySummary,
  kpis: {
    ...emptySummary.kpis,
    document_count: 1248,
    revision_count: 2600,
    source_observation_count: 1900,
    observed_document_count: 1000,
    unobserved_document_count: 248,
    coverage_ratio: 0.8013,
    documents_by_type: { article: 1248 },
    freshness_status_counts: {
      recently_observed: 800,
      aging_observation: 100,
      stale_observation: 80,
      future_timestamp: 2,
      unknown: 266,
    },
  },
  top_topics: [{ term: 'intelligence', document_frequency: 72 }],
}

export const emptyDomains: DomainSummary = {
  as_of: emptySummary.as_of,
  counting_unit: 'unique_current_document',
  total_domains: 0,
  domains: [],
}

export const emptyActivity: RevisionActivity = {
  source_domain: null,
  start: '2026-10-01T00:00:00+00:00',
  end: '2026-10-15T00:00:00+00:00',
  counting_unit: 'revision_snapshots_by_observed_utc_day',
  total_revisions: 0,
  series: [],
  caution: 'Revision observation timestamps are not original publication or crawl-event times.',
}
