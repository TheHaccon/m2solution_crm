import { type FormEvent, useEffect, useRef, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const { user, loading, login, loginWithToken } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const googleHandled = useRef(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [googlePending, setGooglePending] = useState(() => Boolean(searchParams.get('google_token')))

  useEffect(() => {
    if (googleHandled.current) return
    const googleToken = searchParams.get('google_token')
    const googleError = searchParams.get('google_error')
    if (!googleToken && !googleError) return

    googleHandled.current = true
    const next = new URLSearchParams(searchParams)
    next.delete('google_token')
    next.delete('google_error')
    setSearchParams(next, { replace: true })

    if (googleError) {
      setGooglePending(false)
      setError('Google sign-in failed')
      return
    }

    setGooglePending(true)
    setError(null)
    loginWithToken(googleToken)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Google sign-in failed')
      })
      .finally(() => setGooglePending(false))
  }, [loginWithToken, searchParams, setSearchParams])

  if (!loading && !googlePending && user) {
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
            placeholder="you@gmail.com"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={googlePending}
          />
        </label>
        <label className="mt-4 block text-sm font-medium">
          Password
          <input
            className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={googlePending}
          />
        </label>
        {error ? <p className="mt-3 text-sm text-rose-700">{error}</p> : null}
        <button
          type="submit"
          disabled={submitting || googlePending}
          className="mt-6 w-full rounded-lg bg-navy py-2.5 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-60"
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
        <div className="my-4 flex items-center gap-3 text-xs text-ink/40">
          <span className="h-px flex-1 bg-ink/10" />
          or
          <span className="h-px flex-1 bg-ink/10" />
        </div>
        <a
          href="/api/auth/google/start"
          aria-disabled={googlePending || submitting}
          className={`block w-full rounded-lg border border-ink/15 bg-paper py-2.5 text-center text-sm font-medium text-ink hover:border-gold ${
            googlePending || submitting ? 'pointer-events-none opacity-60' : ''
          }`}
        >
          {googlePending ? 'Signing in with Google…' : 'Sign in with Google'}
        </a>
      </form>
    </div>
  )
}
