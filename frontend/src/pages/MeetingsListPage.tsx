import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import { formatDateTime } from '../lib/format'
import type { Meeting } from '../types'

export function MeetingsListPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api<Meeting[]>('/api/meetings')
      .then(setMeetings)
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">Meetings</h1>
          <p className="mt-1 text-ink/55">Internal notes from client conversations. Not shared on invoice links.</p>
        </div>
        <Link to="/meetings/new" className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream hover:bg-navy-2">
          New meeting
        </Link>
      </div>
      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}
      <div className="mt-6 space-y-3">
        {meetings.length === 0 ? <p className="text-ink/45">No meetings yet.</p> : null}
        {meetings.map((m) => (
          <Link key={m.id} to={`/meetings/${m.id}`} className="block rounded-2xl bg-paper p-5 shadow-sm hover:ring-1 hover:ring-ink/10">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="font-medium">{m.title}</p>
              <p className="text-sm text-ink/50">{formatDateTime(m.scheduled_at)}</p>
            </div>
            <p className="mt-1 text-sm text-ink/60">{m.client_name}</p>
            {m.body ? <p className="mt-2 line-clamp-2 text-sm text-ink/55">{m.body}</p> : null}
          </Link>
        ))}
      </div>
    </div>
  )
}
