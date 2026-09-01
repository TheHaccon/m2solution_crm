import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { api } from '../api'
import { toDateTimeLocal } from '../lib/format'
import type { Client, Meeting } from '../types'

export function MeetingFormPage() {
  const { id } = useParams()
  const [search] = useSearchParams()
  const navigate = useNavigate()
  const editing = Boolean(id)
  const [clients, setClients] = useState<Client[]>([])
  const [clientId, setClientId] = useState(search.get('clientId') ?? '')
  const [title, setTitle] = useState('')
  const [scheduledAt, setScheduledAt] = useState(() => toDateTimeLocal(new Date().toISOString()))
  const [attendees, setAttendees] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api<Client[]>('/api/clients').then(setClients).catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!id) return
    api<Meeting>(`/api/meetings/${id}`)
      .then((m) => {
        setClientId(String(m.client_id))
        setTitle(m.title)
        setScheduledAt(toDateTimeLocal(m.scheduled_at))
        setAttendees(m.attendees ?? '')
        setBody(m.body ?? '')
      })
      .catch((err: Error) => setError(err.message))
  }, [id])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    const payload = {
      client_id: Number(clientId),
      title,
      scheduled_at: new Date(scheduledAt).toISOString(),
      attendees: attendees || null,
      body: body || null,
    }
    try {
      if (editing) {
        await api(`/api/meetings/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
        navigate(`/meetings/${id}`)
      } else {
        const created = await api<Meeting>('/api/meetings', { method: 'POST', body: JSON.stringify(payload) })
        navigate(`/meetings/${created.id}`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <p className="text-sm text-ink/50">
        <Link to="/meetings" className="hover:underline">
          Meetings
        </Link>
        <span> / {editing ? 'Edit' : 'New'}</span>
      </p>
      <h1 className="mt-2 font-serif text-3xl">{editing ? 'Edit meeting' : 'New meeting'}</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-2xl bg-paper p-6 shadow-sm">
        <label className="block text-sm font-medium">
          Client
          <select className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" value={clientId} onChange={(e) => setClientId(e.target.value)} required>
            <option value="">Select a client</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-medium">
          Title
          <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label className="block text-sm font-medium">
          Date & time
          <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} required />
        </label>
        <label className="block text-sm font-medium">
          Attendees
          <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" placeholder="Names, comma-separated" value={attendees} onChange={(e) => setAttendees(e.target.value)} />
        </label>
        <label className="block text-sm font-medium">
          Notes (markdown)
          <textarea className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2 font-mono text-sm" rows={10} value={body} onChange={(e) => setBody(e.target.value)} />
          <span className="mt-1 block text-xs text-ink/45">
            Discord-style markdown. Inline <code className="font-mono">`code`</code> and fenced blocks with ``` look like code on the meeting page.
          </span>
        </label>
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream disabled:opacity-60">
            {saving ? 'Saving…' : 'Save'}
          </button>
          <Link to={editing ? `/meetings/${id}` : '/meetings'} className="rounded-lg px-4 py-2 text-sm text-ink/60">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
