import { ApiError } from './client'
import { parseDashboardSummary, parseRevisionActivity } from './dashboard'
import { emptyActivity, emptySummary } from '../../test/fixtures'

describe('dashboard API response handling', () => {
  it('accepts the backend dashboard contracts', () => {
    expect(parseDashboardSummary(emptySummary)).toEqual(emptySummary)
    expect(parseRevisionActivity(emptyActivity)).toEqual(emptyActivity)
  })

  it('classifies structurally invalid JSON separately from network failures', () => {
    expect(() => parseDashboardSummary({ kpis: { document_count: 'many' } })).toThrow(ApiError)
    try {
      parseDashboardSummary({})
    } catch (error) {
      expect(error).toMatchObject({ kind: 'invalid-response' })
    }
  })
})
