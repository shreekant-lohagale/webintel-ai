import { formatInteger, formatPercentage } from './format'

describe('KPI formatting', () => {
  it('formats integer counts for scanning', () => {
    expect(formatInteger(1248050)).toBe('1,248,050')
  })

  it('formats ratios and preserves unavailable coverage', () => {
    expect(formatPercentage(0.8013)).toBe('80%')
    expect(formatPercentage(null)).toBe('—')
  })
})
