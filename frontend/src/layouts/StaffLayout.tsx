import { NavLink, Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/clients', label: 'Clients' },
  { to: '/invoices', label: 'Invoices' },
  { to: '/meetings', label: 'Meetings' },
]

export function StaffLayout() {
  const { user, loading, logout } = useAuth()

  if (loading) {
    return <div className="grid min-h-svh place-items-center text-ink/50">Loading…</div>
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="flex min-h-svh">
      <aside className="no-print flex w-56 shrink-0 flex-col bg-ink text-cream">
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
        <div className="border-t border-white/10 p-4">
          <p className="truncate text-sm text-white/80">{user.full_name}</p>
          <p className="truncate text-xs text-white/40">{user.email}</p>
          <button type="button" onClick={logout} className="mt-3 text-xs text-gold-2 hover:underline">
            Sign out
          </button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-6 sm:p-8">
        <Outlet />
      </main>
    </div>
  )
}
