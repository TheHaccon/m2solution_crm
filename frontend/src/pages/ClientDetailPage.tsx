import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api } from '../api'
import { MarkdownBody } from '../markdown/MarkdownBody'
import { StatusBadge } from '../components/StatusBadge'
import { formatDate, formatDateTime, money } from '../lib/format'
import type { Client, InvoiceList, Meeting } from '../types'

export function ClientDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [client, setClient] = useState<Client | null>(null)
  const [invoices, setInvoices] = useState<InvoiceList[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    Promise.all([
      api<Client>(`/api/clients/${id}`),
      api<InvoiceList[]>(`/api/invoices?client_id=${id}`),
      api<Meeting[]>(`/api/meetings?client_id=${id}`),
    ])
      .then(([c, inv, m]) => {
        setClient(c)
        setInvoices(inv)
        setMeetings(m)
      })
      .catch((err: Error) => setError(err.message))
  }, [id])

  async function onDelete() {
    if (!id || !confirm('Delete this client and related meetings and your invoices? Teammate invoices block delete.')) return
    try {
      await api(`/api/clients/${id}`, { method: 'DELETE' })
      navigate('/clients')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  if (error) return <p className="text-rose-700">{error}</p>
  if (!client) return <p className="text-ink/50">Loading…</p>

  return (
    <div>
      <p className="text-sm text-ink/50">
        <Link to="/clients" className="hover:underline">
          Clients
        </Link>
        <span> / {client.name}</span>
      </p>
      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">{client.name}</h1>
          <p className="mt-1 text-ink/60">{client.email ?? 'No email'} · {client.phone ?? 'No phone'}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to={`/invoices/new?clientId=${client.id}`} className="rounded-lg bg-navy px-3 py-2 text-sm font-medium text-cream">
            New invoice
          </Link>
          <Link to={`/meetings/new?clientId=${client.id}`} className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm">
            New meeting
          </Link>
          <Link to={`/clients/${client.id}/edit`} className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm">
            Edit
          </Link>
          <button type="button" onClick={onDelete} className="rounded-lg px-3 py-2 text-sm text-rose-700">
            Delete
          </button>
        </div>
      </div>

      {client.address || client.notes ? (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {client.address ? (
            <div className="rounded-2xl bg-paper p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wider text-ink/45">Address</p>
              <p className="mt-2 whitespace-pre-line text-sm">{client.address}</p>
            </div>
          ) : null}
          {client.notes ? (
            <div className="rounded-2xl bg-paper p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wider text-ink/45">Notes</p>
              <div className="mt-2 text-sm leading-relaxed">
                <MarkdownBody text={client.notes} />
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl bg-paper p-5 shadow-sm">
          <h2 className="font-medium">Invoices</h2>
          <ul className="mt-3 divide-y divide-ink/8">
            {invoices.length === 0 ? <li className="py-3 text-sm text-ink/45">None yet.</li> : null}
            {invoices.map((inv) => (
              <li key={inv.id} className="flex items-center justify-between py-3">
                <Link to={`/invoices/${inv.id}`} className="hover:underline">
                  {inv.number}
                </Link>
                <div className="flex items-center gap-3">
                  <StatusBadge status={inv.status} />
                  <span className="text-sm tabular-nums">{money(inv.total)}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-2xl bg-paper p-5 shadow-sm">
          <h2 className="font-medium">Meetings</h2>
          <ul className="mt-3 divide-y divide-ink/8">
            {meetings.length === 0 ? <li className="py-3 text-sm text-ink/45">None yet.</li> : null}
            {meetings.map((m) => (
              <li key={m.id} className="py-3">
                <Link to={`/meetings/${m.id}`} className="font-medium hover:underline">
                  {m.title}
                </Link>
                <p className="text-sm text-ink/50">{formatDateTime(m.scheduled_at)}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
      <p className="mt-4 text-xs text-ink/40">Added {formatDate(client.created_at)}</p>
    </div>
  )
}
