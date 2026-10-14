import { Check, Copy, ExternalLink, FileText, Fingerprint, Globe2, UserRound } from 'lucide-react'
import { useState } from 'react'
import { Panel, PanelHeader } from '../../components/ui/Panel'
import { formatDateTime } from '../../lib/format'
import type { WebDocument } from '../../types/documents'

function MetadataItem({ label, value, icon: Icon }: { label: string; value: string; icon: typeof FileText }) {
  return (
    <div className="rounded-xl border border-white/[0.055] bg-black/10 p-3">
      <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-slate-600"><Icon size={12} />{label}</div>
      <p className="mt-2 break-words text-xs leading-5 text-slate-300">{value}</p>
    </div>
  )
}

export function DocumentOverview({ document }: { document: WebDocument }) {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle')
  const copyContent = async () => {
    try {
      await navigator.clipboard.writeText(document.content)
      setCopyStatus('copied')
    } catch {
      setCopyStatus('error')
    }
    window.setTimeout(() => setCopyStatus('idle'), 1500)
  }
  const metadataEntries = Object.entries(document.metadata)

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetadataItem label="Source domain" value={document.source_domain} icon={Globe2} />
        <MetadataItem label="Author" value={document.author ?? 'Not provided'} icon={UserRound} />
        <MetadataItem label="Published" value={document.published_at ? formatDateTime(document.published_at) : 'Not provided'} icon={FileText} />
        <MetadataItem label="Scraped" value={formatDateTime(document.scraped_at)} icon={Fingerprint} />
      </div>

      <Panel>
        <PanelHeader
          title="Current extracted content"
          description="Rendered as plain text. Source content is treated as untrusted input."
          action={
            <button type="button" onClick={() => void copyContent()} className="focus-ring inline-flex items-center gap-2 rounded-lg border border-white/[0.08] px-3 py-2 text-[11px] font-medium text-slate-400 hover:bg-white/[0.04] hover:text-slate-200">
              {copyStatus === 'copied' ? <Check size={14} className="text-teal-300" /> : <Copy size={14} />}{copyStatus === 'copied' ? 'Copied' : copyStatus === 'error' ? 'Copy failed' : 'Copy text'}
            </button>
          }
        />
        <div className="max-h-[560px] overflow-auto p-5 sm:p-6">
          <p className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-300">{document.content}</p>
        </div>
      </Panel>

      <Panel>
        <PanelHeader title="Document metadata" description="Identifiers and fields stored on the current normalized document." />
        <dl className="grid gap-x-8 gap-y-5 p-5 text-xs sm:grid-cols-2 sm:p-6">
          <div><dt className="text-slate-600">Canonical source</dt><dd className="mt-1.5 break-all"><a href={document.source_url} target="_blank" rel="noreferrer" className="focus-ring inline-flex items-start gap-1.5 text-teal-300 hover:underline">{document.source_url}<ExternalLink size={12} className="mt-0.5 shrink-0" /></a></dd></div>
          <div><dt className="text-slate-600">Extraction method</dt><dd className="mt-1.5 text-slate-300">{document.extraction_method}</dd></div>
          <div><dt className="text-slate-600">Document ID</dt><dd className="mt-1.5 break-all font-mono text-[11px] text-slate-400">{document.document_id}</dd></div>
          <div><dt className="text-slate-600">Content hash</dt><dd className="mt-1.5 break-all font-mono text-[11px] text-slate-400">{document.content_hash}</dd></div>
          <div><dt className="text-slate-600">Tags</dt><dd className="mt-2 flex flex-wrap gap-1.5">{document.tags.length ? document.tags.map((tag) => <span key={tag} className="rounded-md bg-white/[0.05] px-2 py-1 text-[10px] text-slate-400">{tag}</span>) : <span className="text-slate-500">None</span>}</dd></div>
          <div><dt className="text-slate-600">Additional metadata</dt><dd className="mt-1.5 text-slate-400">{metadataEntries.length ? <pre className="overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] leading-5">{JSON.stringify(document.metadata, null, 2)}</pre> : 'None'}</dd></div>
        </dl>
      </Panel>
    </div>
  )
}
