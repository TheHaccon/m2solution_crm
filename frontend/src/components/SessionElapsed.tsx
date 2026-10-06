import { formatDuration, sessionSeconds } from '../lib/duration'
import type { TimeSession } from '../types'

export function SessionElapsed({
  session,
  receivedAt,
  nowMs,
}: {
  session: TimeSession
  receivedAt: number
  nowMs: number
}) {
  const seconds = sessionSeconds(session, receivedAt, nowMs)
  if (session.status === 'running') {
    return <span className="tabular-nums">Live elapsed {formatDuration(seconds)}</span>
  }
  return <span className="tabular-nums">Paused {formatDuration(seconds)}</span>
}
