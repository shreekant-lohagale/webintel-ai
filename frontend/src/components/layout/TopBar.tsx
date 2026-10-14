import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Menu, RefreshCw } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { dashboardApi } from '../../lib/api/dashboard'
import { queryKeys } from '../../lib/queryKeys'

const pageMeta: Record<string, { title: string; description: string }> = {
  '/': { title: 'Intelligence Overview', description: 'Signals, coverage, and activity across your intelligence corpus.' },
  '/documents': { title: 'Documents', description: 'Browse and inspect normalized source documents.' },
  '/search': { title: 'Search', description: 'Find evidence across indexed public web sources.' },
  '/assistant': { title: 'AI Assistant', description: 'Ask grounded questions with source-backed answers.' },
  '/topics': { title: 'Topic Intelligence', description: 'Track deterministic keyword patterns and trends.' },
  '/monitoring': { title: 'Source Monitoring', description: 'Review provenance coverage and observation age.' },
  '/settings': { title: 'Settings', description: 'Configure your WebIntel AI workspace.' },
}

export function TopBar({ onMenuOpen }: { onMenuOpen: () => void }) {
  const location = useLocation()
  const queryClient = useQueryClient()
  const meta = pageMeta[location.pathname] ?? pageMeta['/']!
  const health = useQuery({
    queryKey: queryKeys.readiness,
    queryFn: ({ signal }) => dashboardApi.readiness(signal),
    refetchInterval: 30_000,
    retry: 1,
  })
  const isRefreshing = queryClient.isFetching({ queryKey: ['dashboard'] }) > 0

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    void queryClient.invalidateQueries({ queryKey: queryKeys.readiness })
  }

  return (
    <header className="sticky top-0 z-30 border-b border-white/[0.06] bg-ink/80 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-20 max-w-[1600px] items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <button
            className="focus-ring -ml-2 rounded-lg p-2 text-slate-300 hover:bg-white/5 lg:hidden"
            type="button"
            onClick={onMenuOpen}
            aria-label="Open navigation"
          >
            <Menu size={21} />
          </button>
          <div className="min-w-0">
            <h1 className="truncate font-display text-base font-semibold text-slate-50 sm:text-lg">{meta.title}</h1>
            <p className="hidden truncate text-xs text-slate-500 sm:block">{meta.description}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <div
            className="flex h-9 items-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.025] px-3 text-xs"
            title={health.isSuccess ? `Connected to ${health.data.database}` : 'Backend readiness check'}
          >
            <span
              className={`size-2 rounded-full ${
                health.isPending ? 'animate-pulse bg-amber-400' : health.isSuccess ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
            <span className="hidden text-slate-400 sm:inline">
              {health.isPending ? 'Checking' : health.isSuccess ? 'Backend ready' : 'Backend unavailable'}
            </span>
          </div>
          <button
            type="button"
            onClick={refresh}
            disabled={isRefreshing}
            className="focus-ring inline-flex h-9 items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.035] px-3 text-xs font-medium text-slate-300 transition hover:border-white/[0.14] hover:bg-white/[0.07] disabled:cursor-wait disabled:opacity-60"
          >
            <RefreshCw className={isRefreshing ? 'animate-spin' : ''} size={15} aria-hidden="true" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>
    </header>
  )
}
