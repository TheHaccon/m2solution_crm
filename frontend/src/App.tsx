import { Navigate, Route, Routes } from 'react-router-dom'

import { StaffLayout } from './layouts/StaffLayout'
import { ClientDetailPage } from './pages/ClientDetailPage'
import { ClientFormPage } from './pages/ClientFormPage'
import { ClientsListPage } from './pages/ClientsListPage'
import { DashboardPage } from './pages/DashboardPage'
import { InvoiceDetailPage } from './pages/InvoiceDetailPage'
import { InvoiceFormPage } from './pages/InvoiceFormPage'
import { InvoicesListPage } from './pages/InvoicesListPage'
import { LoginPage } from './pages/LoginPage'
import { MeetingDetailPage } from './pages/MeetingDetailPage'
import { MeetingFormPage } from './pages/MeetingFormPage'
import { MeetingsListPage } from './pages/MeetingsListPage'
import { PublicInvoicePage } from './pages/PublicInvoicePage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/i/:token" element={<PublicInvoicePage />} />
      <Route element={<StaffLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/clients" element={<ClientsListPage />} />
        <Route path="/clients/new" element={<ClientFormPage />} />
        <Route path="/clients/:id" element={<ClientDetailPage />} />
        <Route path="/clients/:id/edit" element={<ClientFormPage />} />
        <Route path="/invoices" element={<InvoicesListPage />} />
        <Route path="/invoices/new" element={<InvoiceFormPage />} />
        <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
        <Route path="/invoices/:id/edit" element={<InvoiceFormPage />} />
        <Route path="/meetings" element={<MeetingsListPage />} />
        <Route path="/meetings/new" element={<MeetingFormPage />} />
        <Route path="/meetings/:id" element={<MeetingDetailPage />} />
        <Route path="/meetings/:id/edit" element={<MeetingFormPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
