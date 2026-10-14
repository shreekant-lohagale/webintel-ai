export interface TopicTerm {
  term: string
  document_frequency: number
}

export interface TopicReport {
  source_domain: string | null
  document_count: number
  counting_unit: string
  terms: TopicTerm[]
}

export interface DomainTopic {
  source_domain: string
  document_count: number
  terms: TopicTerm[]
}

export interface DomainTopicsReport {
  document_count: number
  counting_unit: string
  domains: DomainTopic[]
}

export type TopicTrendStatus = 'emerging' | 'disappeared' | 'rising' | 'falling' | 'stable'

export interface TopicTrendTerm {
  term: string
  before_df: number
  after_df: number
  delta: number
  status: TopicTrendStatus
}

export interface TopicTrendsReport {
  source_domain: string | null
  counting_unit: string
  before_start: string
  before_end: string
  after_start: string
  after_end: string
  before_document_count: number
  after_document_count: number
  terms: TopicTrendTerm[]
  total_distinct_terms: number
  caution: string
}

export interface TopicQuery {
  sourceDomain?: string
  limit: number
  ngrams: 1 | 2
  maxDocuments?: number
}

export interface TopicTrendQuery extends TopicQuery {
  beforeStart: string
  beforeEnd: string
  afterStart: string
  afterEnd: string
}
