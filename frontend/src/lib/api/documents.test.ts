import { ApiError } from './client'
import { parseComparison, parseDocument, parseDocumentList, parseRevisions, parseSources, parseTimeline } from './documents'
import { comparisonFixture, documentFixture, documentListFixture, revisionsFixture, sourcesFixture, timelineFixture } from '../../test/documentFixtures'

describe('document API response validation', () => {
  it('accepts every document workspace backend contract', () => {
    expect(parseDocument(documentFixture)).toEqual(documentFixture)
    expect(parseDocumentList(documentListFixture)).toEqual(documentListFixture)
    expect(parseSources(sourcesFixture)).toEqual(sourcesFixture)
    expect(parseRevisions(revisionsFixture)).toEqual(revisionsFixture)
    expect(parseTimeline(timelineFixture)).toEqual(timelineFixture)
    expect(parseComparison(comparisonFixture)).toEqual(comparisonFixture)
  })

  it('reports invalid document and revision payloads distinctly', () => {
    for (const parse of [parseDocument, parseRevisions, parseComparison]) {
      try { parse({ items: 'invalid' }) } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect(error).toMatchObject({ kind: 'invalid-response' })
      }
    }
  })
})
