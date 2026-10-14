import { monitoringDocumentsFixture, monitoringDomainsFixture, monitoringOverviewFixture } from '../../test/intelligenceFixtures'
import { parseMonitoringDocuments, parseMonitoringDomains, parseMonitoringOverview } from './monitoring'

describe('monitoring API validation', () => {
  it('validates overview, document, and domain reports', () => {
    expect(parseMonitoringOverview(monitoringOverviewFixture)).toEqual(monitoringOverviewFixture)
    expect(parseMonitoringDocuments(monitoringDocumentsFixture)).toEqual(monitoringDocumentsFixture)
    expect(parseMonitoringDomains(monitoringDomainsFixture)).toEqual(monitoringDomainsFixture)
  })
  it('rejects unknown freshness categories and malformed coverage', () => {
    expect(() => parseMonitoringDocuments({ ...monitoringDocumentsFixture, items: [{ ...monitoringDocumentsFixture.items[0], status: 'online' }] })).toThrow('monitored document')
    expect(() => parseMonitoringOverview({ ...monitoringOverviewFixture, coverage_ratio: '100%' })).toThrow('monitoring overview')
  })
})
