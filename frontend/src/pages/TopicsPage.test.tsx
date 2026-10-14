import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../app/App'
import { domainTopicsFixture, topicFixture, trendsFixture } from '../test/intelligenceFixtures'

const json = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))
function renderTopics(entry = '/topics') { const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } }); return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[entry]}><App /></MemoryRouter></QueryClientProvider>) }
function topicFetch(input: RequestInfo | URL, init?: RequestInit) { void init; const url = String(input); if (url.includes('/health/')) return json({ status: 'ready', database: 'test' }); if (url.includes('/topics/domains')) return json(domainTopicsFixture); if (url.includes('/topics/trends')) return json(trendsFixture); return json(topicFixture) }

describe('TopicsPage', () => {
  it('renders keyword frequencies and switches unigram/bigram requests', async () => {
    const fetchMock = vi.fn(topicFetch); vi.stubGlobal('fetch', fetchMock); renderTopics()
    expect((await screen.findAllByText('pipeline')).length).toBeGreaterThan(0)
    expect(screen.getByText('Keyword explorer')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Term size'), '2')
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => new URL(String(input), 'http://test').searchParams.get('ngrams') === '2')).toBe(true))
  })

  it('sends source-domain filters and links to filtered documents', async () => {
    const fetchMock = vi.fn(topicFetch); vi.stubGlobal('fetch', fetchMock); renderTopics()
    await screen.findAllByText('pipeline')
    await userEvent.type(screen.getByLabelText('Topic source domain'), '127.0.0.1')
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).includes('source_domain=127.0.0.1'))).toBe(true))
    expect(screen.getByRole('link', { name: 'View documents' })).toHaveAttribute('href', '/documents?domain=127.0.0.1')
  })

  it('validates non-overlapping date windows before requesting trends', async () => {
    const fetchMock = vi.fn(topicFetch); vi.stubGlobal('fetch', fetchMock)
    renderTopics('/topics?before_start=2026-10-01&before_end=2026-10-10&after_start=2026-10-09&after_end=2026-10-15')
    expect(await screen.findByRole('alert')).toHaveTextContent('non-overlapping')
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/topics/trends'))).toBe(false)
  })

  it('renders rising, falling, and unchanged backend statuses', async () => {
    vi.stubGlobal('fetch', vi.fn(topicFetch)); renderTopics()
    expect(await screen.findByText('Rising')).toBeInTheDocument()
    expect(screen.getByText('Absent after')).toBeInTheDocument()
    expect(screen.getByText('Unchanged')).toBeInTheDocument()
  })

  it('handles an empty baseline without claiming public growth', async () => {
    const emptyBaseline = { ...trendsFixture, before_document_count: 0, terms: [{ term: 'new sample term', before_df: 0, after_df: 1, delta: 1, status: 'emerging' }] }
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => String(input).includes('/topics/trends') ? json(emptyBaseline) : topicFetch(input)))
    renderTopics()
    expect(await screen.findByText(/Empty baseline/)).toHaveTextContent('not evidence of growing public interest')
    expect(screen.getByText('Emerging in sample')).toBeInTheDocument()
  })

  it('shows loading, empty, and retry states', async () => {
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => String(input).includes('/health/') ? json({ status: 'ready', database: 'test' }) : new Promise<Response>(() => {})))
    const loading = renderTopics(); expect(loading.container.querySelector('.animate-pulse')).toBeInTheDocument(); loading.unmount()
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => String(input).includes('/topics') ? json({ ...topicFixture, terms: [] }) : json({ status: 'ready', database: 'test' })))
    renderTopics(); expect(await screen.findByText('No keyword frequencies')).toBeInTheDocument()
  })
})
