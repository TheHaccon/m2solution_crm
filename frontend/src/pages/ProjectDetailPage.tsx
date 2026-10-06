import { type FormEvent, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../api'
import { SessionElapsed } from '../components/SessionElapsed'
import { formatDate } from '../lib/format'
import { durationSeconds, formatDuration, useTicker, wholeUnit } from '../lib/duration'
import type { Project, TimeEntry } from '../types'

export function ProjectDetailPage() {
  const { id } = useParams()
  const [project, setProject] = useState<Project | null>(null)
  const [entries, setEntries] = useState<TimeEntry[]>([])
  const [receivedAt, setReceivedAt] = useState(0)
  const [workDate, setWorkDate] = useState<string | null>(null)
  const [hours, setHours] = useState('')
  const [minutes, setMinutes] = useState('')
  const [seconds, setSeconds] = useState('')
  const [note, setNote] = useState('')
  const [stopNote, setStopNote] = useState('')
  const [stopOpen, setStopOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const ticking = project?.my_session?.status === 'running'
  const nowMs = useTicker(ticking)

  useEffect(() => {
    if (!stopOpen) return
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setStopOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [stopOpen])

  function apply(nextProject: Project, nextEntries: TimeEntry[]) {
    setProject(nextProject)
    setEntries(nextEntries)
    setReceivedAt(Date.now())
  }

  useEffect(() => {
    if (!id) return
    let cancelled = false
    Promise.all([api<Project>(`/api/projects/${id}`), api<TimeEntry[]>(`/api/projects/${id}/entries`)])
      .then(([nextProject, nextEntries]) => {
        if (!cancelled) apply(nextProject, nextEntries)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  async function reload() {
    if (!id) return
    const [nextProject, nextEntries] = await Promise.all([
      api<Project>(`/api/projects/${id}`),
      api<TimeEntry[]>(`/api/projects/${id}/entries`),
    ])
    apply(nextProject, nextEntries)
  }

  async function onTimer(action: 'start' | 'pause') {
    if (!id) return
    setError(null)
    setSaving(true)
    try {
      await api(`/api/projects/${id}/timer/${action}`, { method: 'POST' })
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Timer action failed')
    } finally {
      setSaving(false)
    }
  }

  function openStop() {
    setStopNote('')
    setError(null)
    setStopOpen(true)
  }

  function dismissStop() {
    setStopOpen(false)
  }

  async function onStop(event: FormEvent) {
    event.preventDefault()
    if (!id) return
    setError(null)
    setSaving(true)
    try {
      await api(`/api/projects/${id}/timer/stop`, {
        method: 'POST',
        body: JSON.stringify({ note: stopNote.trim() ? stopNote.trim() : null }),
      })
      setStopOpen(false)
      setStopNote('')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Timer action failed')
    } finally {
      setSaving(false)
    }
  }

  async function onAddTime(e: FormEvent) {
    e.preventDefault()
    if (!id || !project) return
    const parsedHours = wholeUnit(hours)
    const parsedMinutes = wholeUnit(minutes)
    const parsedSeconds = wholeUnit(seconds)
    if (parsedHours === null || parsedMinutes === null || parsedSeconds === null) {
      setError('Use whole hours, minutes, and seconds.')
      return
    }
    const duration = durationSeconds(parsedHours, parsedMinutes, parsedSeconds)
    if (duration <= 0) {
      setError('Duration must be greater than zero')
      return
    }
    const date = workDate ?? project.server_today
    if (!date) {
      setError('Choose a date')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await api(`/api/projects/${id}/entries`, {
        method: 'POST',
        body: JSON.stringify({
          work_date: date,
          duration_seconds: duration,
          note: note.trim() ? note.trim() : null,
        }),
      })
      setHours('')
      setMinutes('')
      setSeconds('')
      setNote('')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add time')
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(entryId: number) {
    if (!id || !confirm('Delete this time entry?')) return
    setError(null)
    try {
      await api(`/api/projects/${id}/entries/${entryId}`, { method: 'DELETE' })
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  if (error && !project) return <p className="text-rose-700">{error}</p>
  if (!project) return <p className="text-ink/50">Loading…</p>

  const dateValue = workDate ?? project.server_today

  return (
    <div>
      <p className="text-sm text-ink/50">
        <Link to="/projects" className="hover:underline">
          Projects
        </Link>
        <span> / {project.name}</span>
      </p>
      <h1 className="mt-2 font-serif text-3xl">{project.name}</h1>
      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}
      <div className="mt-6 rounded-2xl bg-paper p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wider text-ink/45">My time</p>
        <p className="mt-2 text-lg tabular-nums">Finished {formatDuration(project.my_finished_seconds)}</p>
        {project.my_session ? (
          <p className="mt-1 text-ink/70">
            <SessionElapsed session={project.my_session} receivedAt={receivedAt} nowMs={nowMs} />
          </p>
        ) : (
          <p className="mt-1 text-sm text-ink/45">No open session</p>
        )}
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={saving}
            onClick={() => void onTimer('start')}
            className="rounded-lg bg-navy px-3 py-2 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-40"
          >
            Start
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => void onTimer('pause')}
            className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm disabled:opacity-40"
          >
            Pause
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={openStop}
            className="rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm disabled:opacity-40"
          >
            Stop
          </button>
        </div>
      </div>

      <form onSubmit={(e) => void onAddTime(e)} className="mt-6 rounded-2xl bg-paper p-5 shadow-sm">
        <h2 className="font-medium">Add time</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-medium">
            Date
            <input
              type="date"
              className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
              value={dateValue}
              onChange={(e) => setWorkDate(e.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium">
            Note
            <input
              className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
        </div>
        <fieldset className="mt-4">
          <legend className="text-sm font-medium">Duration</legend>
          <div className="mt-2 flex flex-wrap gap-3">
            <label className="text-sm text-ink/70">
              Hours
              <input
                type="number"
                min={0}
                step={1}
                inputMode="numeric"
                className="mt-1 w-24 rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={hours}
                onChange={(e) => setHours(e.target.value)}
              />
            </label>
            <label className="text-sm text-ink/70">
              Minutes
              <input
                type="number"
                min={0}
                step={1}
                inputMode="numeric"
                className="mt-1 w-24 rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={minutes}
                onChange={(e) => setMinutes(e.target.value)}
              />
            </label>
            <label className="text-sm text-ink/70">
              Seconds
              <input
                type="number"
                min={0}
                step={1}
                inputMode="numeric"
                className="mt-1 w-24 rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={seconds}
                onChange={(e) => setSeconds(e.target.value)}
              />
            </label>
          </div>
        </fieldset>
        <button
          type="submit"
          disabled={saving}
          className="mt-4 rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-40"
        >
          Add time
        </button>
      </form>

      <section className="mt-6 overflow-hidden rounded-2xl bg-paper shadow-sm">
        <h2 className="px-5 pt-5 font-medium">My finished entries</h2>
        <table className="mt-3 w-full text-sm">
          <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
            <tr>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Duration</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Note</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink/45">
                  No finished entries yet.
                </td>
              </tr>
            ) : null}
            {entries.map((entry) => (
              <tr key={entry.id} className="border-t border-ink/8">
                <td className="px-4 py-3">{formatDate(entry.work_date)}</td>
                <td className="px-4 py-3 tabular-nums">{formatDuration(entry.duration_seconds)}</td>
                <td className="px-4 py-3 text-ink/70">{entry.source}</td>
                <td className="px-4 py-3 text-ink/70">{entry.note ?? '—'}</td>
                <td className="px-4 py-3 text-right">
                  <button type="button" onClick={() => void onDelete(entry.id)} className="text-sm text-rose-700">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {stopOpen ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-navy/50 p-4" onClick={dismissStop}>
          <form
            className="w-full max-w-sm rounded-2xl bg-paper p-5 shadow-lg"
            onClick={(event) => event.stopPropagation()}
            onSubmit={(event) => void onStop(event)}
          >
            <h2 className="font-serif text-xl">Stop timer</h2>
            {project.my_session ? (
              <p className="mt-3 text-ink/70">
                <SessionElapsed session={project.my_session} receivedAt={receivedAt} nowMs={nowMs} />
              </p>
            ) : (
              <p className="mt-3 text-sm text-ink/45">No open session</p>
            )}
            <label className="mt-4 block text-sm text-ink/70">
              Note
              <input
                autoFocus
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={stopNote}
                onChange={(event) => setStopNote(event.target.value)}
              />
            </label>
            {error ? <p className="mt-3 text-rose-700">{error}</p> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-lg border border-ink/15 bg-paper px-3 py-1.5 text-sm hover:bg-ink/5 disabled:opacity-40"
                onClick={dismissStop}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-navy px-3 py-1.5 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-40"
              >
                Stop
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  )
}
