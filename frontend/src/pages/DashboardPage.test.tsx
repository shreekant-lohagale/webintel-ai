import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { App } from '../app/App'
import { emptyActivity, emptyDomains, emptySummary, populatedSummary } from '../test/fixtures'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockRequests(options: { summary?: unknown; domains?: unknown; activity?: unknown; status?: number } = {}) {
  const status = options.status ?? 200
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes('/health/ready')) return Promise.resolve(jsonResponse({ status: 'ready', database: 'webintel_ai' }))
    if (url.includes('/dashboard/summary')) return Promise.resolve(jsonResponse(options.summary ?? emptySummary, status))
    if (url.includes('/dashboard/domains')) return Promise.resolve(jsonResponse(options.domains ?? emptyDomains, status))
    if (url.includes('/dashboard/revision-activity')) return Promise.resolve(jsonResponse(options.activity ?? emptyActivity, status))
    return Promise.resolve(jsonResponse({ detail: 'Not found' }, 404))
  })
}

function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DashboardPage', () => {
  it('shows loading skeletons while HTTP requests are pending', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => undefined)))
    const { container } = renderDashboard()
    expect(screen.getByText('Awaiting data snapshot')).toBeInTheDocument()
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('shows accurate empty states', async () => {
    vi.stubGlobal('fetch', mockRequests())
    renderDashboard()
    expect(await screen.findByText('No revision activity')).toBeInTheDocument()
    expect(screen.getByText('No monitoring data')).toBeInTheDocument()
    expect(screen.getByText('No keyword terms')).toBeInTheDocument()
    expect(screen.getByText('No domains found')).toBeInTheDocument()
  })

  it('keeps widgets available when API requests fail', async () => {
    vi.stubGlobal('fetch', mockRequests({ status: 503 }))
    renderDashboard()
    expect(await screen.findByText(/Summary metrics are unavailable/)).toBeInTheDocument()
    expect(screen.getAllByText('This widget could not load').length).toBeGreaterThanOrEqual(3)
  })

  it('renders real values from successful mocked HTTP responses', async () => {
    vi.stubGlobal('fetch', mockRequests({ summary: populatedSummary }))
    renderDashboard()
    expect(await screen.findByText('1,248')).toBeInTheDocument()
    expect(screen.getByText('80%')).toBeInTheDocument()
    expect(screen.getByText('intelligence')).toBeInTheDocument()
  })
})
