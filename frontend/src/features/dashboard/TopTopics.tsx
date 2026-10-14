import { Hash } from 'lucide-react'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { EmptyState, ErrorState, Skeleton } from '../../components/ui/States'
import { errorMessage } from '../../lib/error'
import type { TopicTerm } from '../../types/dashboard'

interface Props {
  data?: TopicTerm[]
  loading: boolean
  error: Error | null
  onRetry: () => void
}

export function TopTopics({ data, loading, error, onRetry }: Props) {
  const max = Math.max(...(data?.map((topic) => topic.document_frequency) ?? [0]), 1)

  return (
    <Panel>
      <PanelHeader title="Top keyword terms" description="Deterministic frequencies across current documents." />
      {loading ? (
        <div className="space-y-4 p-6">{Array.from({ length: 6 }, (_, index) => <Skeleton key={index} className="h-8 w-full" />)}</div>
      ) : error ? (
        <ErrorState message={errorMessage(error)} onRetry={onRetry} />
      ) : !data?.length ? (
        <EmptyState title="No keyword terms" description="Extracted keyword frequencies will appear when document content is available." />
      ) : (
        <ol className="space-y-4 p-5 sm:p-6">
          {data.map((topic, index) => (
            <li key={topic.term} className="grid grid-cols-[24px_minmax(0,1fr)_auto] items-center gap-3">
              <span className="font-mono text-[10px] text-slate-600">{String(index + 1).padStart(2, '0')}</span>
              <div className="min-w-0">
                <div className="mb-1.5 flex items-center justify-between gap-3">
                  <span className="truncate text-xs font-medium text-slate-300">{topic.term}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.045]">
                  <div className="h-full rounded-full bg-gradient-to-r from-teal-500 to-cyan-300" style={{ width: `${(topic.document_frequency / max) * 100}%` }} />
                </div>
              </div>
              <span className="flex items-center gap-1 font-mono text-[11px] text-slate-500" title="Document frequency">
                <Hash size={11} aria-hidden="true" />{topic.document_frequency}
              </span>
            </li>
          ))}
        </ol>
      )}
    </Panel>
  )
}
