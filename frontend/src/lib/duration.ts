import { useEffect, useState } from 'react'

import type { TimeSession } from '../types'

/** Clock display from whole seconds. Hours are not wrapped at 24. */
export function formatDuration(totalSeconds: number): string {
  const whole = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(whole / 3600)
  const minutes = Math.floor((whole % 3600) / 60)
  const seconds = whole % 60
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${hours}:${pad(minutes)}:${pad(seconds)}`
}

export function wholeUnit(raw: string): number | null {
  const trimmed = raw.trim()
  if (trimmed === '') return 0
  if (!/^\d+$/.test(trimmed)) return null
  return Number(trimmed)
}

export function durationSeconds(hours: number, minutes: number, seconds: number): number {
  return hours * 3600 + minutes * 60 + seconds
}

/**
 * Live elapsed from the server baseline, plus time since this response arrived.
 * A paused session is only its stored accumulated seconds.
 */
export function sessionSeconds(session: TimeSession, receivedAt: number, nowMs: number): number {
  if (session.status !== 'running' || session.segment_started_at == null) {
    return session.accumulated_seconds
  }
  const serverNow = Date.parse(session.server_now)
  const started = Date.parse(session.segment_started_at)
  const baseline = session.accumulated_seconds + (serverNow - started) / 1000
  const since = receivedAt > 0 ? Math.max(0, (nowMs - receivedAt) / 1000) : 0
  return Math.max(0, Math.floor(baseline + since))
}

export function useTicker(enabled: boolean): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!enabled) return
    setNow(Date.now())
    const id = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [enabled])
  return now
}
