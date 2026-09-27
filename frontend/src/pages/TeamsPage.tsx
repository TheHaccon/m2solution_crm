import { type FormEvent, useEffect, useState } from 'react'

import { api } from '../api'
import { useAuth } from '../auth/AuthContext'
import { useTeam } from '../team/TeamContext'
import type { TeamDetail, TeamSummary } from '../types'

export function TeamsPage() {
  const { user } = useAuth()
  const { teams, teamId, setTeamId, refreshTeams } = useTeam()
  const [name, setName] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(teamId)
  const [detail, setDetail] = useState<TeamDetail | null>(null)
  const [memberEmail, setMemberEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (selectedId == null && teams[0]) setSelectedId(teams[0].id)
  }, [selectedId, teams])

  useEffect(() => {
    if (selectedId == null) {
      setDetail(null)
      return
    }
    api<TeamDetail>(`/api/teams/${selectedId}`)
      .then(setDetail)
      .catch((err: Error) => setError(err.message))
  }, [selectedId])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    setError(null)
    try {
      const created = await api<TeamDetail>('/api/teams', {
        method: 'POST',
        body: JSON.stringify({ name: name.trim() }),
      })
      setName('')
      await refreshTeams()
      setTeamId(created.id)
      setSelectedId(created.id)
      setDetail(created)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed')
    } finally {
      setSaving(false)
    }
  }

  async function onAddMember(e: FormEvent) {
    e.preventDefault()
    if (selectedId == null || !memberEmail.trim()) return
    setSaving(true)
    setError(null)
    try {
      const updated = await api<TeamDetail>(`/api/teams/${selectedId}/members`, {
        method: 'POST',
        body: JSON.stringify({ email: memberEmail.trim() }),
      })
      setMemberEmail('')
      setDetail(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Add member failed')
    } finally {
      setSaving(false)
    }
  }

  async function onRemoveMember(userId: number) {
    if (selectedId == null) return
    setSaving(true)
    setError(null)
    try {
      const updated = await api<TeamDetail>(`/api/teams/${selectedId}/members/${userId}`, { method: 'DELETE' })
      setDetail(updated)
      if (userId === user?.id) {
        const list = await refreshTeams()
        if (list[0]) {
          setTeamId(list[0].id)
          setSelectedId(list[0].id)
        } else {
          setSelectedId(null)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Remove failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <h1 className="font-serif text-3xl">Teams</h1>
      <p className="mt-1 text-ink/55">Clients and meeting notes are shared in a team. Invoices stay personal.</p>
      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}

      <form onSubmit={onCreate} className="mt-6 flex flex-wrap items-end gap-3">
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-wider text-ink/45">New team</span>
          <input
            className="mt-1 block w-64 rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Team name"
          />
        </label>
        <button
          type="submit"
          disabled={saving || !name.trim()}
          className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream disabled:opacity-50"
        >
          Create
        </button>
      </form>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl bg-paper p-5 shadow-sm">
          <h2 className="font-medium">Your teams</h2>
          <ul className="mt-3 divide-y divide-ink/8">
            {teams.length === 0 ? <li className="py-3 text-sm text-ink/45">Create a team to get started.</li> : null}
            {teams.map((team: TeamSummary) => (
              <li key={team.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(team.id)}
                  className={`w-full px-1 py-3 text-left text-sm ${selectedId === team.id ? 'font-medium' : 'text-ink/70 hover:text-ink'}`}
                >
                  {team.name}
                  {team.id === teamId ? <span className="ml-2 text-xs text-ink/40">active</span> : null}
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl bg-paper p-5 shadow-sm">
          <h2 className="font-medium">{detail?.name ?? 'Members'}</h2>
          {!detail ? (
            <p className="mt-3 text-sm text-ink/45">Select a team.</p>
          ) : (
            <>
              <ul className="mt-3 divide-y divide-ink/8">
                {detail.members.map((member) => (
                  <li key={member.user_id} className="flex items-center justify-between py-3 text-sm">
                    <div>
                      <p className="font-medium">{member.full_name}</p>
                      <p className="text-ink/50">{member.email}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => onRemoveMember(member.user_id)}
                      className="text-xs text-rose-700 hover:underline"
                    >
                      {member.user_id === user?.id ? 'Leave' : 'Remove'}
                    </button>
                  </li>
                ))}
              </ul>
              <form onSubmit={onAddMember} className="mt-4 flex flex-wrap items-end gap-2">
                <input
                  className="w-full max-w-xs rounded-lg border border-ink/15 bg-cream px-3 py-2 text-sm outline-none focus:border-gold"
                  type="email"
                  placeholder="Existing staff email"
                  value={memberEmail}
                  onChange={(e) => setMemberEmail(e.target.value)}
                />
                <button type="submit" disabled={saving} className="rounded-lg border border-ink/15 px-3 py-2 text-sm">
                  Add member
                </button>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  )
}
