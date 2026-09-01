import { type FormEvent, useState } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const { user, loading, login } = useAuth()
    const [email, setEmail] = useState('admin@m2solution.com')
  const [password, setPassword] = useState('changeme')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) {
    return <Navigate to="/dashboard" replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="grid min-h-svh place-items-center bg-navy px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm rounded-2xl bg-paper p-8 shadow-xl">
        <p className="font-serif text-3xl text-ink">M2 Solution</p>
        <p className="mt-1 text-sm text-ink/55">Staff sign in</p>
        <label className="mt-6 block text-sm font-medium">
          Email
          <input
            className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="mt-4 block text-sm font-medium">
          Password
          <input
            className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error ? <p className="mt-3 text-sm text-rose-700">{error}</p> : null}
        <button
          type="submit"
          disabled={submitting}
          className="mt-6 w-full rounded-lg bg-navy py-2.5 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-60"
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
