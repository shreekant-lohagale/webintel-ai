import {
  Bot,
  FileStack,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
  Radar,
  Search,
  Settings,
  Tags,
  X,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { Brand } from './Brand'

const navigation = [
  { label: 'Overview', to: '/', icon: LayoutDashboard },
  { label: 'Documents', to: '/documents', icon: FileStack },
  { label: 'Search', to: '/search', icon: Search },
  { label: 'AI Assistant', to: '/assistant', icon: Bot },
  { label: 'Topic Intelligence', to: '/topics', icon: Tags },
  { label: 'Source Monitoring', to: '/monitoring', icon: Radar },
  { label: 'Settings', to: '/settings', icon: Settings },
]

interface SidebarProps {
  collapsed: boolean
  mobileOpen: boolean
  onToggle: () => void
  onMobileClose: () => void
}

export function Sidebar({ collapsed, mobileOpen, onToggle, onMobileClose }: SidebarProps) {
  const content = (
    <>
      <div className="flex h-20 items-center justify-between border-b border-white/[0.06] px-5">
        <Brand compact={collapsed} />
        <button
          className="focus-ring hidden rounded-lg p-2 text-slate-500 transition hover:bg-white/5 hover:text-slate-200 lg:block"
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
        </button>
        <button
          className="focus-ring rounded-lg p-2 text-slate-400 hover:bg-white/5 lg:hidden"
          type="button"
          onClick={onMobileClose}
          aria-label="Close navigation"
        >
          <X size={20} />
        </button>
      </div>
      <nav className="flex-1 space-y-1.5 px-3 py-5" aria-label="Primary navigation">
        {navigation.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={onMobileClose}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              `focus-ring group relative flex h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-teal-300/[0.09] text-teal-200'
                  : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-100'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <span className="absolute -left-3 h-5 w-0.5 rounded-r bg-teal-300" />}
                <Icon className="shrink-0" size={18} strokeWidth={1.8} aria-hidden="true" />
                {!collapsed && <span className="whitespace-nowrap">{label}</span>}
              </>
            )}
          </NavLink>
        ))}
      </nav>
      {!collapsed && (
        <div className="m-3 rounded-xl border border-white/[0.06] bg-white/[0.025] p-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Workspace</p>
          <p className="mt-1.5 text-xs text-slate-300">Public web intelligence</p>
          <div className="mt-3 flex items-center gap-2 text-[11px] text-slate-500">
            <span className="size-1.5 rounded-full bg-teal-400" /> Phase 6 · Foundation
          </div>
        </div>
      )}
    </>
  )

  return (
    <>
      <aside
        className={`fixed inset-y-0 left-0 z-40 hidden flex-col border-r border-white/[0.06] bg-[#080e1a]/95 backdrop-blur-xl transition-[width] duration-200 lg:flex ${collapsed ? 'w-[76px]' : 'w-[248px]'}`}
      >
        {content}
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onMobileClose}
            aria-label="Close navigation overlay"
          />
          <aside className="relative flex h-full w-[min(86vw,300px)] flex-col border-r border-white/10 bg-[#080e1a] shadow-2xl">
            {content}
          </aside>
        </div>
      )}
    </>
  )
}
