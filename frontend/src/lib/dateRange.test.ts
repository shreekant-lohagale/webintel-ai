import { revisionDateRange, validateTopicWindows } from './dateRange'

describe('revisionDateRange', () => {
  it('uses inclusive UTC days with an exclusive next-day boundary', () => {
    const result = revisionDateRange(7, new Date('2026-10-14T23:45:00-07:00'))
    expect(result).toEqual({
      start: '2026-10-09T00:00:00.000Z',
      end: '2026-10-16T00:00:00.000Z',
    })
  })

  it('keeps every supported range within the backend 90-day limit', () => {
    const result = revisionDateRange(30, new Date('2026-10-14T12:00:00Z'))
    expect((Date.parse(result.end) - Date.parse(result.start)) / 86_400_000).toBe(30)
  })
})

describe('validateTopicWindows', () => {
  it('converts ordered exclusive-end dates to UTC timestamps', () => {
    expect(validateTopicWindows({ beforeStart: '2026-10-01', beforeEnd: '2026-10-08', afterStart: '2026-10-08', afterEnd: '2026-10-15' }).value).toEqual({ beforeStart: '2026-10-01T00:00:00.000Z', beforeEnd: '2026-10-08T00:00:00.000Z', afterStart: '2026-10-08T00:00:00.000Z', afterEnd: '2026-10-15T00:00:00.000Z' })
  })
  it('rejects overlapping and oversized windows', () => {
    expect(validateTopicWindows({ beforeStart: '2026-10-01', beforeEnd: '2026-10-10', afterStart: '2026-10-09', afterEnd: '2026-10-15' }).error).toContain('non-overlapping')
    expect(validateTopicWindows({ beforeStart: '2025-01-01', beforeEnd: '2025-02-01', afterStart: '2025-02-01', afterEnd: '2026-10-15' }).error).toContain('366')
  })
})
