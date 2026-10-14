import { Blend, BookOpenText, Orbit } from 'lucide-react'
import type { SearchMode } from '../../types/search'

const modes: { value: SearchMode; label: string; short: string; icon: typeof BookOpenText }[] = [
  { value: 'keyword', label: 'Keyword / BM25', short: 'Matches query terms using lexical BM25 ranking.', icon: BookOpenText },
  { value: 'semantic', label: 'Semantic / Vector', short: 'Ranks related meaning using embedding cosine similarity.', icon: Orbit },
  { value: 'hybrid', label: 'Hybrid', short: 'Fuses keyword and semantic ranks using reciprocal rank fusion.', icon: Blend },
]

export function SearchModeSelector({ value, onChange }: { value: SearchMode; onChange: (mode: SearchMode) => void }) {
  return (
    <fieldset>
      <legend className="text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-600">Retrieval mode</legend>
      <div className="mt-3 grid gap-2 md:grid-cols-3">
        {modes.map(({ value: mode, label, short, icon: Icon }) => (
          <label key={mode} className={`focus-within:ring-2 focus-within:ring-teal-300/60 relative flex cursor-pointer items-start gap-3 rounded-xl border p-3.5 transition ${value === mode ? 'border-teal-300/25 bg-teal-300/[0.065]' : 'border-white/[0.06] bg-black/10 hover:border-white/[0.11]'}`}>
            <input type="radio" name="search-mode" value={mode} checked={value === mode} onChange={() => onChange(mode)} className="sr-only" />
            <span className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg ${value === mode ? 'bg-teal-300/10 text-teal-300' : 'bg-white/[0.04] text-slate-500'}`}><Icon size={15} /></span>
            <span><span className={`block text-xs font-medium ${value === mode ? 'text-teal-200' : 'text-slate-300'}`}>{label}</span><span className="mt-1 block text-[10px] leading-4 text-slate-600">{short}</span></span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
