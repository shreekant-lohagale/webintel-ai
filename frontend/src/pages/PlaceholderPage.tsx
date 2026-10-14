import { ArrowRight, Blocks } from 'lucide-react'

export function PlaceholderPage({ section }: { section: string }) {
  return (
    <div className="grid min-h-[calc(100vh-10rem)] place-items-center">
      <div className="max-w-lg text-center">
        <span className="mx-auto grid size-14 place-items-center rounded-2xl border border-teal-300/20 bg-teal-300/[0.07] text-teal-300">
          <Blocks size={24} strokeWidth={1.6} aria-hidden="true" />
        </span>
        <p className="mt-6 text-xs font-semibold uppercase tracking-[0.2em] text-teal-300">Next milestone</p>
        <h2 className="mt-2 font-display text-2xl font-semibold text-white">{section} is taking shape</h2>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          The application foundation is ready. This workspace will connect to the existing WebIntel APIs in its dedicated milestone.
        </p>
        <a href="/" className="focus-ring mt-6 inline-flex items-center gap-2 rounded-lg text-sm font-medium text-slate-300 hover:text-teal-300">
          Return to intelligence overview <ArrowRight size={15} aria-hidden="true" />
        </a>
      </div>
    </div>
  )
}
