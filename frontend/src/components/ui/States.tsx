import { AlertTriangle, Inbox, RotateCcw } from 'lucide-react'

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-white/[0.055] ${className}`} aria-hidden="true" />
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex min-h-44 flex-col items-center justify-center px-6 py-8 text-center" role="alert">
      <span className="grid size-10 place-items-center rounded-xl bg-rose-400/10 text-rose-300">
        <AlertTriangle size={19} aria-hidden="true" />
      </span>
      <p className="mt-3 text-sm font-medium text-slate-200">This widget could not load</p>
      <p className="mt-1 max-w-md text-xs leading-5 text-slate-500">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="focus-ring mt-4 inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-white/5"
      >
        <RotateCcw size={14} aria-hidden="true" /> Retry
      </button>
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex min-h-44 flex-col items-center justify-center px-6 py-8 text-center">
      <span className="grid size-10 place-items-center rounded-xl bg-slate-400/10 text-slate-400">
        <Inbox size={19} aria-hidden="true" />
      </span>
      <p className="mt-3 text-sm font-medium text-slate-200">{title}</p>
      <p className="mt-1 max-w-md text-xs leading-5 text-slate-500">{description}</p>
    </div>
  )
}

