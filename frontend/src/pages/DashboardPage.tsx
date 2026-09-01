import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import { StatusBadge } from '../components/StatusBadge'
import { formatDateTime, money } from '../lib/format'
import type { Dashboard } from '../types'

export function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api<Dashboard>('/api/dashboard')
      .then(setData)
      .catch((err: Error) => setError(err.message))
  }, [])

  if (error) return <p className="text-rose-700">{error}</p>
  if (!data) return <p className="text-ink/50">Loading dashboard…</p>

  const cards = [
    { label: 'Unpaid', value: money(data.unpaid_total), hint: `${data.unpaid_count} sent` },
    { label: 'Drafts', value: String(data.draft_count), hint: 'not sent yet' },
    { label: 'Paid', value: String(data.paid_count), hint: 'marked paid' },
  ]

  return (
    <div>
      <h1 className="font-serif text-3xl">Dashboard</h1>
      <p className="mt-1 text-ink/55">Your invoices and views; meetings for the active team.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className="rounded-2xl bg-paper p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink/45">{card.label}</p>
            <p className="mt-2 font-serif text-3xl">{card.value}</p>
            <p className="mt-1 text-sm text-ink/50">{card.hint}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl bg-paper p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-medium">Recent invoices</h2>
            <Link to="/invoices" className="text-sm text-ink/50 hover:text-ink">
              View all
            </Link>
          </div>
          <ul className="mt-4 divide-y divide-ink/8">
            {data.recent_invoices.length === 0 ? <li className="py-3 text-sm text-ink/45">No invoices yet.</li> : null}
            {data.recent_invoices.map((inv) => (
              <li key={inv.id} className="flex items-center justify-between gap-3 py-3">
                <div>
                  <Link to={`/invoices/${inv.id}`} className="font-medium hover:underline">
                    {inv.number}
                  </Link>
                  <p className="text-sm text-ink/50">{inv.client_name}</p>
                </div>
                <div className="text-right">
                  <StatusBadge status={inv.status} />
                  <p className="mt-1 text-sm tabular-nums">{money(inv.total)}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl bg-paper p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-medium">Recent meetings</h2>
            <Link to="/meetings" className="text-sm text-ink/50 hover:text-ink">
              View all
            </Link>
          </div>
          <ul className="mt-4 divide-y divide-ink/8">
            {data.recent_meetings.length === 0 ? <li className="py-3 text-sm text-ink/45">No meetings yet.</li> : null}
            {data.recent_meetings.map((m) => (
              <li key={m.id} className="py-3">
                <Link to={`/meetings/${m.id}`} className="font-medium hover:underline">
                  {m.title}
                </Link>
                <p className="text-sm text-ink/50">
                  {m.client_name} · {formatDateTime(m.scheduled_at)}
                </p>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="mt-6 rounded-2xl bg-paper p-5 shadow-sm">
        <h2 className="font-medium">Invoice views</h2>
        <ul className="mt-4 divide-y divide-ink/8">
          {data.recent_views.length === 0 ? <li className="py-3 text-sm text-ink/45">No public views yet.</li> : null}
          {data.recent_views.map((v, i) => (
            <li key={`${v.invoice_id}-${v.viewed_at}-${i}`} className="flex items-center justify-between py-3 text-sm">
              <Link to={`/invoices/${v.invoice_id}`} className="hover:underline">
                {v.invoice_number} · {v.client_name}
              </Link>
              <span className="text-ink/50">{formatDateTime(v.viewed_at)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
