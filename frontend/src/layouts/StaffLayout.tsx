import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'

import { api } from '../api'
import { useAuth } from '../auth/AuthContext'
import { TeamProvider, useTeam } from '../team/TeamContext'
import { useTheme } from '../theme/ThemeContext'

const ADMIN_EMAIL = 'admin@m2solution.com'

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/clients', label: 'Clients' },
  { to: '/projects', label: 'Projects' },
  { to: '/invoices', label: 'Invoices' },
  { to: '/expenses', label: 'Expenses' },
  { to: '/accounting', label: 'Accounting' },
  { to: '/meetings', label: 'Meetings' },
  { to: '/files', label: 'Files' },
]

function StaffShell() {
  const { user, logout } = useAuth()
  const { teams, teamId, loading, setTeamId } = useTeam()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [passwordOpen, setPasswordOpen] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordOk, setPasswordOk] = useState(false)
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [resetOpen, setResetOpen] = useState(false)
  const [resetTargetEmail, setResetTargetEmail] = useState('')
  const [resetNewPassword, setResetNewPassword] = useState('')
  const [resetConfirmPassword, setResetConfirmPassword] = useState('')
  const [resetError, setResetError] = useState<string | null>(null)
  const [resetOk, setResetOk] = useState(false)
  const [resetSaving, setResetSaving] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const isAdmin = (user?.email ?? '').toLowerCase() === ADMIN_EMAIL
  const activeTeam = teams.find((t) => t.id === teamId)

  useEffect(() => {
    if (!menuOpen && !passwordOpen && !resetOpen) return
    function onPointer(e: MouseEvent) {
      if (menuOpen && menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false)
    }
    function onKey(e: KeyboardEvent) {
      if (e.key !== 'Escape') return
      if (passwordOpen) setPasswordOpen(false)
      else if (resetOpen) setResetOpen(false)
      else setMenuOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [menuOpen, passwordOpen, resetOpen])

  useEffect(() => {
    setMenuOpen(false)
    setPasswordOpen(false)
    setResetOpen(false)
  }, [location.pathname, teamId])

  function openPassword() {
    setMenuOpen(false)
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
    setPasswordError(null)
    setPasswordOk(false)
    setPasswordOpen(true)
  }

  function openReset() {
    setMenuOpen(false)
    setResetTargetEmail('')
    setResetNewPassword('')
    setResetConfirmPassword('')
    setResetError(null)
    setResetOk(false)
    setResetOpen(true)
  }

  async function onAdminReset(e: FormEvent) {
    e.preventDefault()
    setResetError(null)
    setResetOk(false)
    if (resetNewPassword !== resetConfirmPassword) {
      setResetError('New passwords do not match')
      return
    }
    if (resetNewPassword.length < 8) {
      setResetError('New password must be at least 8 characters')
      return
    }
    setResetSaving(true)
    try {
      await api('/api/auth/admin/password-reset', {
        method: 'POST',
        body: JSON.stringify({ email: resetTargetEmail, new_password: resetNewPassword }),
      })
      setResetTargetEmail('')
      setResetNewPassword('')
      setResetConfirmPassword('')
      setResetOk(true)
    } catch (err) {
      setResetError(err instanceof Error ? err.message : 'Could not reset password')
    } finally {
      setResetSaving(false)
    }
  }

  async function onChangePassword(e: FormEvent) {
    e.preventDefault()
    setPasswordError(null)
    setPasswordOk(false)
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match')
      return
    }
    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters')
      return
    }
    setPasswordSaving(true)
    try {
      await api('/api/auth/password', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setPasswordOk(true)
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : 'Could not change password')
    } finally {
      setPasswordSaving(false)
    }
  }

  if (loading) {
    return <div className="grid min-h-svh place-items-center text-ink/50">Loading…</div>
  }
  if (teams.length === 0 && location.pathname !== '/teams') {
    return <Navigate to="/teams" replace />
  }

  return (
    <div className="flex h-svh min-h-0 print:h-auto">
      <aside className="no-print sticky top-0 flex h-svh w-56 shrink-0 flex-col bg-navy text-cream">
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
                <button
                  type="button"
                  onClick={openPassword}
                  className="block w-full rounded-lg px-2 py-1.5 text-left text-sm text-ink/70 hover:bg-ink/10 hover:text-ink"
                >
                  Change password
                </button>
                {isAdmin ? (
                  <button
                    type="button"
                    onClick={openReset}
                    className="block w-full rounded-lg px-2 py-1.5 text-left text-sm text-ink/70 hover:bg-ink/10 hover:text-ink"
                  >
                    Reset staff password
                  </button>
                ) : null}
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
      <main className="min-h-0 min-w-0 flex-1 overflow-y-auto p-6 sm:p-8 print:overflow-visible">
        <Outlet key={teamId ?? 'none'} />
      </main>
      {passwordOpen ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-navy/50 p-4"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setPasswordOpen(false)
          }}
        >
          <form className="w-full max-w-sm rounded-2xl bg-paper p-5 text-ink shadow-lg" onSubmit={(e) => void onChangePassword(e)}>
            <h2 className="font-serif text-xl">Change password</h2>
            <label className="mt-4 block text-sm text-ink/70">
              Current password
              <input
                autoFocus
                type="password"
                autoComplete="current-password"
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </label>
            <label className="mt-3 block text-sm text-ink/70">
              New password
              <input
                type="password"
                autoComplete="new-password"
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
              />
            </label>
            <label className="mt-3 block text-sm text-ink/70">
              Re-enter new password
              <input
                type="password"
                autoComplete="new-password"
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </label>
            {passwordError ? <p className="mt-3 text-sm text-rose-700">{passwordError}</p> : null}
            {passwordOk ? <p className="mt-3 text-sm text-ink/70">Password updated.</p> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-lg border border-ink/15 bg-paper px-3 py-1.5 text-sm hover:bg-ink/5"
                onClick={() => setPasswordOpen(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={passwordSaving}
                className="rounded-lg bg-navy px-3 py-1.5 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-40"
              >
                {passwordSaving ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      ) : null}
      {resetOpen ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-navy/50 p-4"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setResetOpen(false)
          }}
        >
          <form className="w-full max-w-sm rounded-2xl bg-paper p-5 text-ink shadow-lg" onSubmit={(e) => void onAdminReset(e)}>
            <h2 className="font-serif text-xl">Reset staff password</h2>
            <label className="mt-4 block text-sm text-ink/70">
              Staff email
              <input
                autoFocus
                type="email"
                autoComplete="off"
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={resetTargetEmail}
                onChange={(e) => setResetTargetEmail(e.target.value)}
                required
              />
            </label>
            <label className="mt-3 block text-sm text-ink/70">
              New password
              <input
                type="password"
                autoComplete="new-password"
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={resetNewPassword}
                onChange={(e) => setResetNewPassword(e.target.value)}
                required
                minLength={8}
              />
            </label>
            <label className="mt-3 block text-sm text-ink/70">
              Re-enter new password
              <input
                type="password"
                autoComplete="new-password"
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={resetConfirmPassword}
                onChange={(e) => setResetConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </label>
            {resetError ? <p className="mt-3 text-sm text-rose-700">{resetError}</p> : null}
            {resetOk ? <p className="mt-3 text-sm text-ink/70">Password updated.</p> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-lg border border-ink/15 bg-paper px-3 py-1.5 text-sm hover:bg-ink/5"
                onClick={() => setResetOpen(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={resetSaving}
                className="rounded-lg bg-navy px-3 py-1.5 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-40"
              >
                {resetSaving ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      ) : null}
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
