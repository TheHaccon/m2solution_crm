import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { TeamProvider, useTeam } from '../team/TeamContext'
import { useTheme } from '../theme/ThemeContext'

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/clients', label: 'Clients' },
  { to: '/invoices', label: 'Invoices' },
  { to: '/meetings', label: 'Meetings' },
]

function StaffShell() {
  const { user, logout } = useAuth()
  const { teams, teamId, loading, setTeamId } = useTeam()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const activeTeam = teams.find((t) => t.id === teamId)

  useEffect(() => {
    if (!menuOpen) return
    function onPointer(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false)
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [menuOpen])

  useEffect(() => {
    setMenuOpen(false)
  }, [location.pathname, teamId])

  if (loading) {
    return <div className="grid min-h-svh place-items-center text-ink/50">Loading…</div>
  }
  if (teams.length === 0 && location.pathname !== '/teams') {
    return <Navigate to="/teams" replace />
  }

  return (
    <div className="flex min-h-svh">
      <aside className="no-print flex w-56 shrink-0 flex-col bg-navy text-cream">
        <div className="border-b border-white/10 px-5 py-6">
          <p className="font-serif text-xl text-gold-2">M2 Solution</p>
          <p className="mt-0.5 text-xs uppercase tracking-[0.18em] text-white/40">CRM</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm transition ${isActive ? 'bg-white/10 text-gold-2' : 'text-white/70 hover:bg-white/5 hover:text-white'}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="relative border-t border-white/10 p-3" ref={menuRef}>
          {menuOpen ? (
            <div className="absolute bottom-full left-3 right-3 mb-2 overflow-hidden rounded-xl bg-paper text-ink shadow-lg">
              <p className="px-3 pt-3 text-[10px] font-semibold uppercase tracking-wider text-ink/40">Team</p>
              <ul className="mt-1 max-h-48 overflow-y-auto py-1">
                {teams.length === 0 ? (
                  <li className="px-3 py-2 text-sm text-ink/45">No team yet.</li>
                ) : (
                  teams.map((team) => (
                    <li key={team.id}>
                      <button
                        type="button"
                        onClick={() => setTeamId(team.id)}
                        className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-ink/10 ${
                          team.id === teamId ? 'font-medium text-ink' : 'text-ink/70'
                        }`}
                      >
                        <span className="truncate">{team.name}</span>
                        {team.id === teamId ? <span className="text-[10px] uppercase tracking-wider text-ink/40">Active</span> : null}
                      </button>
                    </li>
                  ))
                )}
              </ul>
              <div className="border-t border-ink/10 p-2">
                <button
                  type="button"
                  role="switch"
                  aria-checked={theme === 'dark'}
                  aria-pressed={theme === 'dark'}
                  onClick={toggleTheme}
                  className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-sm text-ink/70 hover:bg-ink/10 hover:text-ink"
                >
                  Dark mode
                  <span
                    className={`relative h-5 w-9 rounded-full transition ${theme === 'dark' ? 'bg-navy' : 'bg-ink/20'}`}
                  >
                    <span
                      className={`absolute top-0.5 h-4 w-4 rounded-full bg-paper shadow transition ${
                        theme === 'dark' ? 'left-4' : 'left-0.5'
                      }`}
                    />
                  </span>
                </button>
                <Link
                  to="/teams"
                  className="block rounded-lg px-2 py-1.5 text-sm text-ink/70 hover:bg-ink/10 hover:text-ink"
                >
                  Manage teams
                </Link>
                <button
                  type="button"
                  onClick={logout}
                  className="mt-0.5 block w-full rounded-lg px-2 py-1.5 text-left text-sm text-rose-700 hover:bg-ink/10"
                >
                  Sign out
                </button>
              </div>
            </div>
          ) : null}
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            className="w-full rounded-lg px-2 py-2 text-left transition hover:bg-white/5"
          >
            <p className="truncate text-sm text-white/80">{user?.full_name}</p>
            <p className="truncate text-xs text-white/40">{user?.email}</p>
            {activeTeam ? (
              <p className="mt-1 truncate text-[11px] text-gold-2/80">{activeTeam.name}</p>
            ) : null}
          </button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-6 sm:p-8">
        <Outlet key={teamId ?? 'none'} />
      </main>
    </div>
  )
}

export function StaffLayout() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="grid min-h-svh place-items-center text-ink/50">Loading…</div>
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }

  return (
    <TeamProvider>
      <StaffShell />
    </TeamProvider>
  )
}
