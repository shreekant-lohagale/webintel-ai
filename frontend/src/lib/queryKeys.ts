export const queryKeys = {
  readiness: ['health', 'readiness'] as const,
  dashboard: {
    summary: ['dashboard', 'summary'] as const,
    domains: ['dashboard', 'domains'] as const,
    revisionActivity: (days: number, start: string, end: string) =>
      ['dashboard', 'revision-activity', { days, start, end }] as const,
  },
}
