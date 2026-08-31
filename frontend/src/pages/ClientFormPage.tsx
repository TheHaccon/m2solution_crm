import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api } from '../api'
import type { Client } from '../types'

export function ClientFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const editing = Boolean(id)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!id) return
    api<Client>(`/api/clients/${id}`)
      .then((c) => {
        setName(c.name)
        setEmail(c.email ?? '')
        setPhone(c.phone ?? '')
        setAddress(c.address ?? '')
        setNotes(c.notes ?? '')
      })
      .catch((err: Error) => setError(err.message))
  }, [id])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    const body = {
      name,
      email: email || null,
      phone: phone || null,
      address: address || null,
      notes: notes || null,
    }
    try {
      if (editing) {
        await api(`/api/clients/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
        navigate(`/clients/${id}`)
      } else {
        const created = await api<Client>('/api/clients', { method: 'POST', body: JSON.stringify(body) })
        navigate(`/clients/${created.id}`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-xl">
      <p className="text-sm text-ink/50">
        <Link to="/clients" className="hover:underline">
          Clients
        </Link>
        <span> / {editing ? 'Edit' : 'New'}</span>
      </p>
      <h1 className="mt-2 font-serif text-3xl">{editing ? 'Edit client' : 'New client'}</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-2xl bg-paper p-6 shadow-sm">
        <label className="block text-sm font-medium">
          Name
          <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className="block text-sm font-medium">
          Email
          <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="block text-sm font-medium">
          Phone
          <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </label>
        <label className="block text-sm font-medium">
          Address
          <textarea className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" rows={3} value={address} onChange={(e) => setAddress(e.target.value)} />
        </label>
        <label className="block text-sm font-medium">
          Internal notes
          <textarea className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-cream disabled:opacity-60">
            {saving ? 'Saving…' : 'Save'}
          </button>
          <Link to={editing ? `/clients/${id}` : '/clients'} className="rounded-lg px-4 py-2 text-sm text-ink/60">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
