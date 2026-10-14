export const queryKeys = {
  readiness: ['health', 'readiness'] as const,
  dashboard: {
    summary: ['dashboard', 'summary'] as const,
    domains: ['dashboard', 'domains'] as const,
    revisionActivity: (days: number, start: string, end: string) =>
      ['dashboard', 'revision-activity', { days, start, end }] as const,
  },
  documents: {
    all: ['documents'] as const,
    list: (params: object) => ['documents', 'list', params] as const,
    detail: (documentId: string) => ['documents', 'detail', documentId] as const,
    sources: (documentId: string) => ['documents', 'sources', documentId] as const,
    revisions: (documentId: string) => ['documents', 'revisions', documentId] as const,
    timeline: (documentId: string) => ['documents', 'timeline', documentId] as const,
    comparison: (documentId: string, from: string, to: string) =>
      ['documents', 'comparison', documentId, from, to] as const,
  },
  search: {
    all: ['search'] as const,
    results: (request: object) => ['search', 'results', request] as const,
  },
  assistant: {
    all: ['assistant'] as const,
  },
  topics: {
    all: ['topics'] as const,
    terms: (params: object) => ['topics', 'terms', params] as const,
    domains: (params: object) => ['topics', 'domains', params] as const,
    trends: (params: object) => ['topics', 'trends', params] as const,
  },
  monitoring: {
    all: ['monitoring'] as const,
    overview: (params: object) => ['monitoring', 'overview', params] as const,
    documents: (params: object) => ['monitoring', 'documents', params] as const,
    domains: (params: object) => ['monitoring', 'domains', params] as const,
  },
}
