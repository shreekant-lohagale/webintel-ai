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

export interface TopicDateWindows {
  beforeStart: string
  beforeEnd: string
  afterStart: string
  afterEnd: string
}

export function validateTopicWindows(windows: TopicDateWindows): { value?: TopicDateWindows; error?: string } {
  const parsed = Object.fromEntries(Object.entries(windows).map(([key, value]) => [key, new Date(`${value}T00:00:00.000Z`)])) as Record<keyof TopicDateWindows, Date>
  if (Object.values(parsed).some((date) => Number.isNaN(date.getTime()))) return { error: 'Choose four valid UTC dates.' }
  if (!(parsed.beforeStart < parsed.beforeEnd && parsed.beforeEnd <= parsed.afterStart && parsed.afterStart < parsed.afterEnd)) return { error: 'Windows must be ordered, non-overlapping, and each contain at least one UTC day.' }
  if ((parsed.afterEnd.getTime() - parsed.beforeStart.getTime()) / 86_400_000 > 366) return { error: 'The overall trend horizon cannot exceed 366 days.' }
  return { value: { beforeStart: parsed.beforeStart.toISOString(), beforeEnd: parsed.beforeEnd.toISOString(), afterStart: parsed.afterStart.toISOString(), afterEnd: parsed.afterEnd.toISOString() } }
}
