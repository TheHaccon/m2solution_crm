import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api } from '../api'
import { formatDateTime } from '../lib/format'
import { MarkdownBody } from '../markdown/MarkdownBody'
import type { Meeting } from '../types'

export function MeetingDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    api<Meeting>(`/api/meetings/${id}`)
      .then(setMeeting)
      .catch((err: Error) => setError(err.message))
  }, [id])

  async function onDelete() {
    if (!id || !confirm('Delete this meeting note?')) return
    try {
      await api(`/api/meetings/${id}`, { method: 'DELETE' })
      navigate('/meetings')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  if (error) return <p className="text-rose-700">{error}</p>
  if (!meeting) return <p className="text-ink/50">Loading…</p>

  return (
    <div className="max-w-3xl">
      <p className="text-sm text-ink/50">
        <Link to="/meetings" className="hover:underline">
          Meetings
        </Link>
        <span> / {meeting.title}</span>
      </p>
      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">{meeting.title}</h1>
          <p className="mt-1 text-ink/60">
            <Link to={`/clients/${meeting.client_id}`} className="hover:underline">
              {meeting.client_name}
            </Link>
            {' · '}
            {formatDateTime(meeting.scheduled_at)}
          </p>
          {meeting.attendees ? <p className="mt-1 text-sm text-ink/50">Attendees: {meeting.attendees}</p> : null}
        </div>
        <div className="flex gap-2">
          <Link to={`/meetings/${meeting.id}/edit`} className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm">
            Edit
          </Link>
          <button type="button" onClick={onDelete} className="rounded-lg px-3 py-2 text-sm text-rose-700">
            Delete
          </button>
        </div>
      </div>
      <article className="mt-6 rounded-2xl bg-paper p-6 text-sm leading-relaxed shadow-sm">
        {meeting.body ? <MarkdownBody text={meeting.body} /> : <p className="text-ink/45">No notes recorded.</p>}
      </article>
    </div>
  )
}
