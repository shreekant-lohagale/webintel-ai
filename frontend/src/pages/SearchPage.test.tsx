import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { App } from '../app/App'
import { documentId } from '../test/documentFixtures'
import { searchFixture, unsafeExcerpt } from '../test/searchFixtures'

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
const healthResponse = () => Promise.resolve(response({ status: 'ready', database: 'webintel_ai' }))

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location-search" className="hidden">{location.search}</output>
}

function renderSearch(entry = '/search') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[entry]}><App /><LocationProbe /></MemoryRouter></QueryClientProvider>)
}

function successfulFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  void init
  return String(input).includes('/health/') ? healthResponse() : Promise.resolve(response(searchFixture))
}

describe('SearchPage', () => {
  it('shows a useful pre-search state and validates an empty query', async () => {
    const fetchMock = vi.fn(successfulFetch)
    vi.stubGlobal('fetch', fetchMock)
    renderSearch()
    expect(screen.getByText('Search the intelligence corpus')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Enter a search query')
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/api/v1/search'))).toHaveLength(0)
  })

  it('submits a POST request from the keyboard and renders result navigation', async () => {
    const fetchMock = vi.fn(successfulFetch)
    vi.stubGlobal('fetch', fetchMock)
    renderSearch()
    const input = screen.getByPlaceholderText('Search indexed intelligence…')
    await userEvent.type(input, 'intelligence pipelines{enter}')
    expect(await screen.findByText('Reliable Intelligence Pipelines')).toBeInTheDocument()
    const searchCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/api/v1/search'))
    expect(searchCall?.[1]).toMatchObject({ method: 'POST' })
    expect(JSON.parse(String(searchCall?.[1]?.body))).toMatchObject({ query: 'intelligence pipelines', mode: 'hybrid', limit: 10 })
    expect(screen.getByRole('link', { name: 'View document' })).toHaveAttribute('href', `/documents/${documentId}`)
  })

  it('synchronizes mode and controls with URL parameters', async () => {
    const fetchMock = vi.fn(successfulFetch)
    vi.stubGlobal('fetch', fetchMock)
    renderSearch('/search?q=intelligence&mode=semantic&limit=20&type=article')
    expect(await screen.findByText('Reliable Intelligence Pipelines')).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Semantic/ })).toBeChecked()
    expect(screen.getByLabelText('Result count')).toHaveValue('20')
    await userEvent.click(screen.getByRole('radio', { name: /Keyword/ }))
    await waitFor(() => expect(screen.getByTestId('location-search')).toHaveTextContent('mode=keyword'))
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => {
      if (!init?.body) return false
      return JSON.parse(String(init.body)).mode === 'keyword'
    })).toBe(true))
  })

  it('shows loading and empty result states', async () => {
    let resolveSearch: ((value: Response) => void) | undefined
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => String(input).includes('/health/') ? healthResponse() : new Promise<Response>((resolve) => { resolveSearch = resolve })))
    renderSearch()
    fireEvent.change(screen.getByPlaceholderText('Search indexed intelligence…'), { target: { value: 'nothing' } })
    await userEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(await screen.findByText('Retrieving indexed evidence…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    resolveSearch?.(response({ query: 'nothing', mode: 'hybrid', count: 0, results: [] }))
    expect(await screen.findByText('No indexed matches')).toBeInTheDocument()
  })

  it('shows API errors and retries the same search', async () => {
    let searchCount = 0
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      if (String(input).includes('/health/')) return healthResponse()
      searchCount += 1
      return Promise.resolve(searchCount <= 2 ? response({ detail: 'Search database unavailable' }, 503) : response(searchFixture))
    }))
    renderSearch('/search?q=intelligence')
    expect(await screen.findByText('Search service unavailable', {}, { timeout: 3000 })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Retry search' }))
    expect(await screen.findByText('Reliable Intelligence Pipelines')).toBeInTheDocument()
  })

  it('renders untrusted excerpts as text without creating HTML elements', async () => {
    vi.stubGlobal('fetch', vi.fn(successfulFetch))
    const { container } = renderSearch('/search?q=intelligence')
    expect(await screen.findByText(unsafeExcerpt)).toBeInTheDocument()
    expect(container.querySelector('img')).not.toBeInTheDocument()
  })

  it('cancels an obsolete request when retrieval mode changes', async () => {
    let firstSignal: AbortSignal | undefined
    let requestNumber = 0
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes('/health/')) return healthResponse()
      requestNumber += 1
      if (requestNumber === 1) {
        firstSignal = init?.signal ?? undefined
        return new Promise<Response>((_resolve, reject) => firstSignal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true }))
      }
      return Promise.resolve(response({ ...searchFixture, mode: 'keyword', results: searchFixture.results.map((hit) => ({ ...hit, hybrid_score: null })) }))
    }))
    renderSearch('/search?q=intelligence&mode=hybrid')
    await waitFor(() => expect(firstSignal).toBeDefined())
    await userEvent.click(screen.getByRole('radio', { name: /Keyword/ }))
    await waitFor(() => expect(firstSignal?.aborted).toBe(true))
    expect(await screen.findByText('Reliable Intelligence Pipelines')).toBeInTheDocument()
  })
})
