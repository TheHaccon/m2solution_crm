import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import type { Client } from '../types'

export function ClientsListPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [q, setQ] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const params = q ? `?q=${encodeURIComponent(q)}` : ''
    api<Client[]>(`/api/clients${params}`)
      .then(setClients)
      .catch((err: Error) => setError(err.message))
  }, [q])

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">Clients</h1>
          <p className="mt-1 text-ink/55">Companies and people you bill and meet with.</p>
        </div>
        <Link to="/clients/new" className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-cream hover:bg-ink-2">
          New client
        </Link>
      </div>
      <input
        className="mt-6 w-full max-w-md rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
        placeholder="Search name or email"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}
      <div className="mt-4 overflow-hidden rounded-2xl bg-paper shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Phone</th>
            </tr>
          </thead>
          <tbody>
            {clients.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-ink/45">
                  No clients yet.
                </td>
              </tr>
            ) : null}
            {clients.map((c) => (
              <tr key={c.id} className="border-t border-ink/8 hover:bg-cream/60">
                <td className="px-4 py-3">
                  <Link to={`/clients/${c.id}`} className="font-medium hover:underline">
                    {c.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink/70">{c.email ?? '—'}</td>
                <td className="px-4 py-3 text-ink/70">{c.phone ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
