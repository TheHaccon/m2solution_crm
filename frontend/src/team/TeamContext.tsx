import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import { api, clearStoredTeamId, getStoredTeamId, setStoredTeamId } from '../api'
import { useAuth } from '../auth/AuthContext'
import type { TeamSummary } from '../types'

type TeamContextValue = {
  teams: TeamSummary[]
  teamId: number | null
  loading: boolean
  setTeamId: (id: number) => void
  refreshTeams: () => Promise<TeamSummary[]>
}

const TeamContext = createContext<TeamContextValue | null>(null)

export function TeamProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [teams, setTeams] = useState<TeamSummary[]>([])
  const [teamId, setTeamIdState] = useState<number | null>(getStoredTeamId)
  const [loading, setLoading] = useState(true)

  const refreshTeams = useCallback(async () => {
    const list = await api<TeamSummary[]>('/api/teams')
    setTeams(list)
    const stored = getStoredTeamId()
    const valid = list.some((t) => t.id === stored)
    if (list.length === 0) {
      clearStoredTeamId()
      setTeamIdState(null)
    } else if (!valid) {
      setStoredTeamId(list[0].id)
      setTeamIdState(list[0].id)
    } else {
      setTeamIdState(stored)
    }
    return list
  }, [])

  useEffect(() => {
    if (!user) {
      setTeams([])
      setLoading(false)
      return
    }
    setLoading(true)
    refreshTeams()
      .catch(() => setTeams([]))
      .finally(() => setLoading(false))
  }, [user, refreshTeams])

  const setTeamId = useCallback((id: number) => {
    setStoredTeamId(id)
    setTeamIdState(id)
  }, [])

  const value = useMemo(
    () => ({ teams, teamId, loading, setTeamId, refreshTeams }),
    [teams, teamId, loading, setTeamId, refreshTeams],
  )
  return <TeamContext.Provider value={value}>{children}</TeamContext.Provider>
}

export function useTeam(): TeamContextValue {
  const ctx = useContext(TeamContext)
  if (!ctx) throw new Error('useTeam must be used within TeamProvider')
  return ctx
}
