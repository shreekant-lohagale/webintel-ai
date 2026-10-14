import { domainTopicsFixture, topicFixture, trendsFixture } from '../../test/intelligenceFixtures'
import { parseDomainTopics, parseTopicReport, parseTopicTrends } from './topics'

describe('topic API validation', () => {
  it('validates topic, domain, and trend reports', () => {
    expect(parseTopicReport(topicFixture)).toEqual(topicFixture)
    expect(parseDomainTopics(domainTopicsFixture)).toEqual(domainTopicsFixture)
    expect(parseTopicTrends(trendsFixture)).toEqual(trendsFixture)
  })
  it('rejects unknown trend classifications and malformed frequencies', () => {
    expect(() => parseTopicReport({ ...topicFixture, terms: [{ term: 'x', document_frequency: 'many' }] })).toThrow('topic term')
    expect(() => parseTopicTrends({ ...trendsFixture, terms: [{ ...trendsFixture.terms[0], status: 'viral' }] })).toThrow('trend row')
  })
})
