export type RevisionRangeDays = 7 | 14 | 30

export interface UtcDateRange {
  start: string
  end: string
}

export function revisionDateRange(days: RevisionRangeDays, now = new Date()): UtcDateRange {
  const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1))
  const start = new Date(end)
  start.setUTCDate(start.getUTCDate() - days)
  return { start: start.toISOString(), end: end.toISOString() }
}
