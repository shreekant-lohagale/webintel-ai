import { ApiError } from './client'
import { parseSearchResponse } from './search'
import { searchFixture } from '../../test/searchFixtures'

describe('search API response validation', () => {
  it('parses the exact hybrid search contract', () => {
    expect(parseSearchResponse(searchFixture)).toEqual(searchFixture)
  })

  it('rejects invalid scores, counts, and unsafe source URLs', () => {
    const invalidPayloads = [
      { ...searchFixture, count: 2 },
      { ...searchFixture, results: [{ ...searchFixture.results[0], semantic_score: 'high' }] },
      { ...searchFixture, results: [{ ...searchFixture.results[0], source_url: 'javascript:alert(1)' }] },
    ]
    for (const payload of invalidPayloads) {
      try { parseSearchResponse(payload) } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect(error).toMatchObject({ kind: 'invalid-response' })
      }
    }
  })
})
