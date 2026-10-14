import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { DashboardPage } from '../pages/DashboardPage'
import { DocumentDetailPage } from '../pages/DocumentDetailPage'
import { DocumentsPage } from '../pages/DocumentsPage'
import { PlaceholderPage } from '../pages/PlaceholderPage'

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/:documentId" element={<DocumentDetailPage />} />
        <Route path="search" element={<PlaceholderPage section="Search" />} />
        <Route path="assistant" element={<PlaceholderPage section="AI Assistant" />} />
        <Route path="topics" element={<PlaceholderPage section="Topic Intelligence" />} />
        <Route path="monitoring" element={<PlaceholderPage section="Source Monitoring" />} />
        <Route path="settings" element={<PlaceholderPage section="Settings" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
