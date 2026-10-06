import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import { SessionElapsed } from '../components/SessionElapsed'
import { formatDuration, useTicker } from '../lib/duration'
import type { Project } from '../types'

export function ProjectsListPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [receivedAt, setReceivedAt] = useState(0)
  const [name, setName] = useState('')
  const [renamingId, setRenamingId] = useState<number | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const ticking = projects.some((project) => project.my_session?.status === 'running')
  const nowMs = useTicker(ticking)

  function applyProjects(rows: Project[]) {
    setProjects(rows)
    setReceivedAt(Date.now())
  }

  useEffect(() => {
    let cancelled = false
    api<Project[]>('/api/projects')
      .then((rows) => {
        if (!cancelled) applyProjects(rows)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function reload() {
    const rows = await api<Project[]>('/api/projects')
    applyProjects(rows)
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await api('/api/projects', { method: 'POST', body: JSON.stringify({ name }) })
      setName('')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create project')
    } finally {
      setSaving(false)
    }
  }

  async function onRename(e: FormEvent, projectId: number) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await api(`/api/projects/${projectId}`, {
        method: 'PATCH',
        body: JSON.stringify({ name: renameValue }),
      })
      setRenamingId(null)
      setRenameValue('')
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not rename project')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div>
        <h1 className="font-serif text-3xl">Projects</h1>
        <p className="mt-1 text-ink/55">Shared names for this team. Hours shown are only yours.</p>
      </div>
      <form onSubmit={(e) => void onCreate(e)} className="mt-6 flex max-w-xl flex-wrap items-end gap-3">
        <label className="min-w-0 flex-1 text-sm font-medium">
          Name
          <input
            className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={255}
            required
          />
        </label>
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-40"
        >
          Create
        </button>
      </form>
      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}
      <div className="mt-4 overflow-hidden rounded-2xl bg-paper shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Finished</th>
              <th className="px-4 py-3 font-medium">Session</th>
            </tr>
          </thead>
          <tbody>
            {projects.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-ink/45">
                  No projects yet.
                </td>
              </tr>
            ) : null}
            {projects.map((project) => (
              <tr key={project.id} className="border-t border-ink/8 hover:bg-ink/5">
                <td className="px-4 py-3">
                  {renamingId === project.id ? (
                    <form onSubmit={(e) => void onRename(e, project.id)} className="flex flex-wrap items-center gap-2">
                      <input
                        className="w-48 rounded-lg border border-ink/15 bg-paper px-3 py-1.5 outline-none focus:border-gold"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        maxLength={255}
                        required
                        autoFocus
                      />
                      <button type="submit" disabled={saving} className="rounded-lg bg-navy px-3 py-1.5 text-sm text-cream">
                        Save
                      </button>
                      <button
                        type="button"
                        className="rounded-lg border border-ink/15 bg-paper px-3 py-1.5 text-sm"
                        onClick={() => setRenamingId(null)}
                      >
                        Cancel
                      </button>
                    </form>
                  ) : (
                    <div className="flex flex-wrap items-center gap-3">
                      <Link to={`/projects/${project.id}`} className="font-medium hover:underline">
                        {project.name}
                      </Link>
                      <button
                        type="button"
                        className="text-sm text-ink/55 hover:text-ink"
                        onClick={() => {
                          setRenamingId(project.id)
                          setRenameValue(project.name)
                        }}
                      >
                        Rename
                      </button>
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 tabular-nums text-ink/80">
                  Finished {formatDuration(project.my_finished_seconds)}
                </td>
                <td className="px-4 py-3 text-ink/70">
                  {project.my_session ? (
                    <SessionElapsed session={project.my_session} receivedAt={receivedAt} nowMs={nowMs} />
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
