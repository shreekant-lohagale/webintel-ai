import { Sparkles } from 'lucide-react'

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3 overflow-hidden">
      <span className="grid size-9 shrink-0 place-items-center rounded-xl border border-teal-300/25 bg-teal-300/10 text-teal-300 shadow-[0_0_24px_-8px_rgba(45,212,191,0.8)]">
        <Sparkles aria-hidden="true" size={18} strokeWidth={1.8} />
      </span>
      {!compact && (
        <span className="min-w-0 whitespace-nowrap font-display text-[15px] font-semibold tracking-tight text-white">
          WebIntel <span className="text-teal-300">AI</span>
        </span>
      )}
    </div>
  )
}
