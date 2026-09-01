import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { InvoiceDocument } from '../components/InvoiceDocument'
import type { PublicInvoice } from '../types'

export function PublicInvoicePage() {
  const { token } = useParams()
  const [invoice, setInvoice] = useState<PublicInvoice | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    let viewer = localStorage.getItem('invoice_viewer')
    if (!viewer) {
      viewer = crypto.randomUUID()
      localStorage.setItem('invoice_viewer', viewer)
    }
    fetch(`/api/public/invoices/${token}`, {
      credentials: 'include',
      headers: { 'X-Viewer-Id': viewer },
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as { detail?: string }
          throw new Error(body.detail || 'Invoice not found')
        }
        return res.json() as Promise<PublicInvoice>
      })
      .then(setInvoice)
      .catch((err: Error) => setError(err.message))
  }, [token])

  if (error) {
    return (
      <div className="force-light grid min-h-svh place-items-center bg-cream px-4">
        <div className="text-center">
          <p className="font-serif text-2xl">Invoice unavailable</p>
          <p className="mt-2 text-ink/55">{error}</p>
        </div>
      </div>
    )
  }

  if (!invoice) {
    return <div className="force-light grid min-h-svh place-items-center bg-cream text-ink/50">Loading invoice…</div>
  }

  return (
    <div className="force-light min-h-svh bg-cream px-4 py-10">
      <div className="no-print mx-auto mb-6 flex max-w-3xl items-center justify-between">
        <p className="font-serif text-lg text-ink">{invoice.company_name}</p>
        <button type="button" onClick={() => window.print()} className="rounded-lg bg-navy px-3 py-1.5 text-sm text-cream">
          Print
        </button>
      </div>
      <InvoiceDocument
        companyName={invoice.company_name}
        companyEmail={invoice.company_email}
        companyAddress={invoice.company_address}
        companyPhone={invoice.company_phone}
        clientName={invoice.client_name}
        clientEmail={invoice.client_email}
        clientAddress={invoice.client_address}
        number={invoice.number}
        status={invoice.status}
        issueDate={invoice.issue_date}
        dueDate={invoice.due_date}
        notes={invoice.notes}
        lineItems={invoice.line_items}
        subtotal={invoice.subtotal}
        total={invoice.total}
      />
    </div>
  )
}
