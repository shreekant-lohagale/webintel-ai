import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { DashboardPage } from '../pages/DashboardPage'
import { DocumentDetailPage } from '../pages/DocumentDetailPage'
import { DocumentsPage } from '../pages/DocumentsPage'
import { PlaceholderPage } from '../pages/PlaceholderPage'
import { SearchPage } from '../pages/SearchPage'
import { AssistantPage } from '../pages/AssistantPage'
import { TopicsPage } from '../pages/TopicsPage'
import { MonitoringPage } from '../pages/MonitoringPage'

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:documentId" element={<DocumentDetailPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="topics" element={<TopicsPage />} />
        <Route path="monitoring" element={<MonitoringPage />} />
        <Route path="settings" element={<PlaceholderPage section="Settings" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
