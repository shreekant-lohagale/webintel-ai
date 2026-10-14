import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../app/App'
import { monitoringDocumentsFixture, monitoringDomainsFixture, monitoringOverviewFixture, unsafeDocumentTitle } from '../test/intelligenceFixtures'

vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>()
  const { TestResponsiveContainer } = await import('../test/ResponsiveContainerMock')
  return { ...actual, ResponsiveContainer: TestResponsiveContainer }
})

const json = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))
function renderMonitoring(entry = '/monitoring?as_of=2026-10-14T18%3A00') { const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } }); return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[entry]}><App /></MemoryRouter></QueryClientProvider>) }
function monitoringFetch(input: RequestInfo | URL, init?: RequestInit) { void init; const url = String(input); if (url.includes('/health/')) return json({ status: 'ready', database: 'test' }); if (url.includes('/monitoring/overview')) return json(monitoringOverviewFixture); if (url.includes('/monitoring/documents')) return json(monitoringDocumentsFixture); return json(monitoringDomainsFixture) }

describe('MonitoringPage', () => {
  it('renders freshness categories, coverage, links, and untrusted metadata safely', async () => {
    vi.stubGlobal('fetch', vi.fn(monitoringFetch)); const { container } = renderMonitoring()
    expect((await screen.findAllByText('100%')).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Aging observation/).length).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: unsafeDocumentTitle })).toHaveAttribute('href', `/documents/${monitoringDocumentsFixture.items[0]!.document_id}`)
    expect(container.querySelector('img')).not.toBeInTheDocument()
    expect(screen.getByText('playwright, scrapy')).toBeInTheDocument()
  })

  it('uses one fixed as_of timestamp for every monitoring endpoint', async () => {
    const fetchMock = vi.fn(monitoringFetch); vi.stubGlobal('fetch', fetchMock); renderMonitoring()
    await screen.findAllByText('100%')
    const calls = fetchMock.mock.calls.filter(([input]) => String(input).includes('/analytics/monitoring/'))
    expect(calls).toHaveLength(3)
    expect(calls.every(([input]) => new URL(String(input), 'http://test').searchParams.get('as_of') === '2026-10-14T18:00:00.000Z')).toBe(true)
  })

  it('applies backend-supported domain and freshness filters', async () => {
    const fetchMock = vi.fn(monitoringFetch); vi.stubGlobal('fetch', fetchMock); renderMonitoring()
    await screen.findAllByText('100%')
    await userEvent.type(screen.getByLabelText('Monitoring source domain'), '127.0.0.1')
    await userEvent.selectOptions(screen.getByLabelText('Freshness category'), 'aging_observation')
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => { const url = new URL(String(input), 'http://test'); return url.pathname.endsWith('/monitoring/documents') && url.searchParams.get('source_domain') === '127.0.0.1' && url.searchParams.get('status') === 'aging_observation' })).toBe(true))
  })

  it('validates freshness thresholds without displaying fake metrics', async () => {
    const fetchMock = vi.fn(monitoringFetch); vi.stubGlobal('fetch', fetchMock); renderMonitoring('/monitoring?as_of=2026-10-14T18%3A00&fresh=200&stale=100')
    expect(await screen.findByRole('alert')).toHaveTextContent('Fresh threshold must be lower')
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/analytics/monitoring/'))).toBe(false)
    expect(screen.queryByText('100%')).not.toBeInTheDocument()
  })

  it('shows empty records and retries an independently failed widget', async () => {
    let overviewCalls = 0
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => { const url = String(input); if (url.includes('/health/')) return json({ status: 'ready', database: 'test' }); if (url.includes('/overview')) { overviewCalls += 1; return overviewCalls === 1 ? json({ detail: 'Analytics database unavailable' }, 503) : json(monitoringOverviewFixture) } if (url.includes('/documents')) return json({ ...monitoringDocumentsFixture, total_matching: 0, items: [] }); return json(monitoringDomainsFixture) }))
    renderMonitoring()
    expect(await screen.findByText('No matching monitoring records')).toBeInTheDocument()
    expect(screen.getByText('This widget could not load')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() => expect(screen.getAllByText('100%').length).toBeGreaterThan(0))
  })
})
