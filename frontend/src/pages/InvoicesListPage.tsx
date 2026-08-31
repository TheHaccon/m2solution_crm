import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import { StatusBadge } from '../components/StatusBadge'
import { formatDate, money } from '../lib/format'
import type { InvoiceList } from '../types'

const filters = ['', 'draft', 'sent', 'paid', 'void'] as const

export function InvoicesListPage() {
  const [invoices, setInvoices] = useState<InvoiceList[]>([])
  const [status, setStatus] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const qs = status ? `?status=${status}` : ''
    api<InvoiceList[]>(`/api/invoices${qs}`)
      .then(setInvoices)
      .catch((err: Error) => setError(err.message))
  }, [status])

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">Invoices</h1>
          <p className="mt-1 text-ink/55">Create, send a share link, mark paid. No in-app payments.</p>
        </div>
        <Link to="/invoices/new" className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-cream hover:bg-ink-2">
          New invoice
        </Link>
      </div>
      <div className="mt-6 flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f || 'all'}
            type="button"
            onClick={() => setStatus(f)}
            className={`rounded-full px-3 py-1 text-sm ${status === f ? 'bg-ink text-cream' : 'bg-paper text-ink/70'}`}
          >
            {f || 'all'}
          </button>
        ))}
      </div>
      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}
      <div className="mt-4 overflow-hidden rounded-2xl bg-paper shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
            <tr>
              <th className="px-4 py-3 font-medium">Number</th>
              <th className="px-4 py-3 font-medium">Client</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Issued</th>
              <th className="px-4 py-3 text-right font-medium">Total</th>
              <th className="px-4 py-3 text-right font-medium">Views</th>
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink/45">
                  No invoices yet.
                </td>
              </tr>
            ) : null}
            {invoices.map((inv) => (
              <tr key={inv.id} className="border-t border-ink/8 hover:bg-cream/60">
                <td className="px-4 py-3">
                  <Link to={`/invoices/${inv.id}`} className="font-medium hover:underline">
                    {inv.number}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <Link to={`/clients/${inv.client_id}`} className="text-ink/70 hover:underline">
                    {inv.client_name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={inv.status} />
                </td>
                <td className="px-4 py-3 text-ink/70">{formatDate(inv.issue_date)}</td>
                <td className="px-4 py-3 text-right tabular-nums">{money(inv.total)}</td>
                <td className="px-4 py-3 text-right tabular-nums">{inv.view_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
