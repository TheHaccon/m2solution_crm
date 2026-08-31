import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api } from '../api'
import { InvoiceDocument } from '../components/InvoiceDocument'
import { formatDateTime } from '../lib/format'
import type { Invoice, InvoiceView } from '../types'

export function InvoiceDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [views, setViews] = useState<InvoiceView[]>([])
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [busy, setBusy] = useState(false)

  async function load() {
    if (!id) return
    const inv = await api<Invoice>(`/api/invoices/${id}`)
    setInvoice(inv)
    const history = await api<InvoiceView[]>(`/api/invoices/${id}/views`)
    setViews(history)
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message))
  }, [id])

  async function action(path: string) {
    if (!id) return
    setBusy(true)
    setError(null)
    try {
      await api(`/api/invoices/${id}/${path}`, { method: 'POST' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  async function copyLink() {
    if (!invoice?.share_url) return
    await navigator.clipboard.writeText(invoice.share_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  async function onDelete() {
    if (!id || !confirm('Delete this draft invoice?')) return
    try {
      await api(`/api/invoices/${id}`, { method: 'DELETE' })
      navigate('/invoices')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  if (error && !invoice) return <p className="text-rose-700">{error}</p>
  if (!invoice) return <p className="text-ink/50">Loading…</p>

  return (
    <div>
      <p className="text-sm text-ink/50">
        <Link to="/invoices" className="hover:underline">
          Invoices
        </Link>
        <span> / {invoice.number}</span>
      </p>
      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">{invoice.number}</h1>
          <p className="mt-1 text-ink/60">
            <Link to={`/clients/${invoice.client_id}`} className="hover:underline">
              {invoice.client_name}
            </Link>
            {' · '}
            {invoice.view_count} view{invoice.view_count === 1 ? '' : 's'}
            {invoice.last_viewed_at ? ` · last ${formatDateTime(invoice.last_viewed_at)}` : ''}
          </p>
        </div>
        <div className="no-print flex flex-wrap gap-2">
          {invoice.status === 'draft' ? (
            <>
              <button type="button" disabled={busy} onClick={() => action('send')} className="rounded-lg bg-ink px-3 py-2 text-sm font-medium text-cream">
                Send (create link)
              </button>
              <Link to={`/invoices/${invoice.id}/edit`} className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm">
                Edit
              </Link>
              <button type="button" onClick={onDelete} className="rounded-lg px-3 py-2 text-sm text-rose-700">
                Delete
              </button>
            </>
          ) : null}
          {invoice.status === 'sent' ? (
            <>
              <button type="button" disabled={busy} onClick={() => action('mark-paid')} className="rounded-lg bg-ink px-3 py-2 text-sm font-medium text-cream">
                Mark paid
              </button>
              <button type="button" disabled={busy} onClick={() => action('void')} className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm">
                Void
              </button>
            </>
          ) : null}
        </div>
      </div>
      {error ? <p className="mt-3 text-sm text-rose-700">{error}</p> : null}

      {invoice.share_url && invoice.status !== 'void' ? (
        <div className="no-print mt-4 flex flex-wrap items-center gap-3 rounded-2xl bg-paper p-4 shadow-sm">
          <code className="min-w-0 flex-1 truncate text-sm">{invoice.share_url}</code>
          <button type="button" onClick={copyLink} className="rounded-lg bg-ink px-3 py-1.5 text-sm text-cream">
            {copied ? 'Copied' : 'Copy link'}
          </button>
          <button type="button" disabled={busy} onClick={() => action('rotate-link')} className="text-sm text-ink/50 hover:text-ink">
            Rotate link
          </button>
        </div>
      ) : (
        <p className="no-print mt-4 text-sm text-ink/50">Send this invoice to generate a public share link. Clients do not sign in.</p>
      )}

      <div className="mt-8">
        <InvoiceDocument
          companyName="M2 Solution"
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
          showStatus
        />
      </div>

      <section className="no-print mt-8 rounded-2xl bg-paper p-5 shadow-sm">
        <h2 className="font-medium">View history</h2>
        <ul className="mt-3 divide-y divide-ink/8 text-sm">
          {views.length === 0 ? <li className="py-3 text-ink/45">No client views yet.</li> : null}
          {views.map((v) => (
            <li key={v.id} className="flex justify-between gap-4 py-3">
              <span>{formatDateTime(v.viewed_at)}</span>
              <span className="truncate text-ink/45">{v.user_agent ?? '—'}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
