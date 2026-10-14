import { UserRound } from 'lucide-react'
import type { AssistantTurn } from '../../types/assistant'
import { AssistantMessage } from './AssistantMessage'

export function MessageList({ turns, onRetry }: { turns: AssistantTurn[]; onRetry: (turn: AssistantTurn) => void }) {
  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 px-4 py-6 sm:px-6" aria-live="polite">
      {turns.map((turn) => <section key={turn.id} className="space-y-3">
        <div className="flex justify-end gap-3"><div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-slate-200 px-4 py-3 text-sm leading-6 text-slate-900 sm:max-w-[75%]">{turn.request.question}</div><span className="grid size-8 shrink-0 place-items-center rounded-xl bg-white/[0.06] text-slate-400"><UserRound size={15} /></span></div>
        <AssistantMessage turn={turn} onRetry={onRetry} />
      </section>)}
    </div>
  )
}
