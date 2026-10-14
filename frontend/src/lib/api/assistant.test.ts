import { answeredFixture, askRequestFixture, abstainedFixture } from '../../test/assistantFixtures'
import { ApiError } from './client'
import { assistantApi, parseAskResponse } from './assistant'

describe('assistant API', () => {
  it('parses grounded answered and abstained responses', () => {
    expect(parseAskResponse(answeredFixture)).toEqual(answeredFixture)
    expect(parseAskResponse(abstainedFixture)).toEqual(abstainedFixture)
  })

  it('rejects answered responses without citations', () => {
    expect(() => parseAskResponse({ ...answeredFixture, citations: [] })).toThrow(ApiError)
  })

  it('rejects citations with unsafe source protocols', () => {
    const citation = { ...answeredFixture.citations[0], source_url: 'javascript:alert(1)' }
    expect(() => parseAskResponse({
      ...answeredFixture,
      citations: [citation],
      claims: [{ ...answeredFixture.claims[0], citations: [citation] }],
    })).toThrow('citation does not match')
  })

  it('rejects abstentions that include unsupported evidence', () => {
    expect(() => parseAskResponse({ ...abstainedFixture, citations: answeredFixture.citations })).toThrow(ApiError)
  })

  it('aborts and reports a timed-out provider request', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn((_input: RequestInfo | URL, init?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
    })))

    const request = assistantApi.ask(askRequestFixture, undefined, 10)
    const rejection = expect(request).rejects.toMatchObject({ kind: 'timeout' })
    await vi.advanceTimersByTimeAsync(11)
    await rejection
    vi.useRealTimers()
  })
})
