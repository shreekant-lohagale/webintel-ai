import { lazy, Suspense, type ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { DocumentDetailPage } from '../pages/DocumentDetailPage'
import { DocumentsPage } from '../pages/DocumentsPage'
import { SearchPage } from '../pages/SearchPage'
import { AssistantPage } from '../pages/AssistantPage'

const DashboardPage = lazy(() => import('../pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const TopicsPage = lazy(() => import('../pages/TopicsPage').then((module) => ({ default: module.TopicsPage })))
const MonitoringPage = lazy(() => import('../pages/MonitoringPage').then((module) => ({ default: module.MonitoringPage })))
const SettingsPage = lazy(() => import('../pages/SettingsPage').then((module) => ({ default: module.SettingsPage })))

function WorkspaceFallback() {
  return <div className="space-y-4" role="status" aria-label="Loading workspace"><div className="h-8 w-52 animate-pulse rounded-lg bg-white/[0.055]" /><div className="h-64 animate-pulse rounded-2xl bg-white/[0.04]" /></div>
}

const deferred = (page: ReactNode) => <Suspense fallback={<WorkspaceFallback />}>{page}</Suspense>

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={deferred(<DashboardPage />)} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:documentId" element={<DocumentDetailPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="topics" element={deferred(<TopicsPage />)} />
        <Route path="monitoring" element={deferred(<MonitoringPage />)} />
        <Route path="settings" element={deferred(<SettingsPage />)} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
