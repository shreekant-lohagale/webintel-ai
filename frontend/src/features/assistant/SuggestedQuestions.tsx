import { ArrowUpRight, Lightbulb } from 'lucide-react'

const suggestions = [
  'What are reliable data engineering pipelines?',
  'How are AI workflows used in modern business?',
  'What does the indexed content say about human review?',
]

export function SuggestedQuestions({ onSelect }: { onSelect: (question: string) => void }) {
  return (
    <section className="mx-auto w-full max-w-3xl px-4 py-10 text-center sm:py-14">
      <span className="mx-auto grid size-12 place-items-center rounded-2xl border border-teal-300/15 bg-teal-300/[0.06] text-teal-300"><Lightbulb size={21} /></span>
      <h2 className="mt-5 font-display text-xl font-semibold text-slate-100">Ask the indexed corpus</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">Answers are generated only from retrieved source evidence. Each accepted claim must include a backend-verified quotation.</p>
      <div className="mt-6 grid gap-2 text-left sm:grid-cols-3">
        {suggestions.map((question) => <button key={question} type="button" onClick={() => onSelect(question)} className="focus-ring group flex min-h-24 items-start justify-between gap-3 rounded-xl border border-white/[0.065] bg-white/[0.018] p-4 text-left text-xs leading-5 text-slate-400 transition hover:border-teal-300/15 hover:bg-teal-300/[0.035] hover:text-slate-200"><span>{question}</span><ArrowUpRight size={13} className="mt-0.5 shrink-0 text-slate-600 group-hover:text-teal-300" /></button>)}
      </div>
    </section>
  )
}
