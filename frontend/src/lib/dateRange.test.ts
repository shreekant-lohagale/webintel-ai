import { revisionDateRange } from './dateRange'

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
