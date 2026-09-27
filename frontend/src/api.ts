const TOKEN_KEY = 'm2_token'
const TEAM_KEY = 'm2_team_id'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function getStoredTeamId(): number | null {
  const raw = localStorage.getItem(TEAM_KEY)
  if (!raw) return null
  const id = Number(raw)
  return Number.isFinite(id) ? id : null
}

export function setStoredTeamId(id: number): void {
  localStorage.setItem(TEAM_KEY, String(id))
}

export function clearStoredTeamId(): void {
  localStorage.removeItem(TEAM_KEY)
}

function detailMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  return fallback
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const teamId = getStoredTeamId()
  if (teamId !== null && !path.startsWith('/api/auth/') && !path.startsWith('/api/public/')) {
    headers.set('X-Team-Id', String(teamId))
  }

  const res = await fetch(path, { ...options, headers, credentials: 'include' })
  if (res.status === 401 && !path.startsWith('/api/auth/login')) {
    clearToken()
    if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/i/')) {
      window.location.href = '/login'
    }
  }
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: unknown }
    throw new Error(detailMessage(err.detail, res.statusText))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}
