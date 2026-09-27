import { type FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { api } from '../api'
import { money, todayISO } from '../lib/format'
import type { Client, Invoice, LineItemInput } from '../types'

const emptyItem = (): LineItemInput => ({ description: '', quantity: 1, unit_price: 0 })

export function InvoiceFormPage() {
  const { id } = useParams()
  const [search] = useSearchParams()
  const navigate = useNavigate()
  const editing = Boolean(id)
  const [clients, setClients] = useState<Client[]>([])
  const [clientId, setClientId] = useState(search.get('clientId') ?? '')
  const [issueDate, setIssueDate] = useState(todayISO())
  const [dueDate, setDueDate] = useState('')
  const [notes, setNotes] = useState('')
  const [items, setItems] = useState<LineItemInput[]>([emptyItem()])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api<Client[]>('/api/clients').then(setClients).catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!id) return
    api<Invoice>(`/api/invoices/${id}`)
      .then((inv) => {
        setClientId(String(inv.client_id))
        setIssueDate(inv.issue_date)
        setDueDate(inv.due_date ?? '')
        setNotes(inv.notes ?? '')
        setItems(
          inv.line_items.map((li) => ({
            description: li.description,
            quantity: Number(li.quantity),
            unit_price: Number(li.unit_price),
          })),
        )
      })
      .catch((err: Error) => setError(err.message))
  }, [id])

  const total = useMemo(
    () => items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0),
    [items],
  )

  function updateItem(index: number, patch: Partial<LineItemInput>) {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const line_items = items.filter((item) => item.description.trim())
    if (line_items.length === 0) {
      setError('Add at least one line item')
      return
    }
    setSaving(true)
    setError(null)
    const body = {
      client_id: Number(clientId),
      issue_date: issueDate,
      due_date: dueDate || null,
      notes: notes || null,
      line_items,
    }
    try {
      if (editing) {
        await api(`/api/invoices/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
        navigate(`/invoices/${id}`)
      } else {
        const created = await api<Invoice>('/api/invoices', { method: 'POST', body: JSON.stringify(body) })
        navigate(`/invoices/${created.id}`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <p className="text-sm text-ink/50">
        <Link to="/invoices" className="hover:underline">
          Invoices
        </Link>
        <span> / {editing ? 'Edit draft' : 'New'}</span>
      </p>
      <h1 className="mt-2 font-serif text-3xl">{editing ? 'Edit draft invoice' : 'New invoice'}</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-5 rounded-2xl bg-paper p-6 shadow-sm">
        <label className="block text-sm font-medium">
          Client
          <select
            className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            required
            disabled={editing}
          >
            <option value="">Select a client</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-medium">
            Issue date
            <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" type="date" value={issueDate} onChange={(e) => setIssueDate(e.target.value)} required />
          </label>
          <label className="block text-sm font-medium">
            Due date
            <input className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </label>
        </div>

        <div>
          <p className="text-sm font-medium">Line items</p>
          <div className="mt-2 space-y-2">
            {items.map((item, index) => (
              <div key={index} className="grid grid-cols-[1fr_5rem_7rem_auto] items-center gap-2">
                <input
                  className="rounded-lg border border-ink/15 px-3 py-2 text-sm"
                  placeholder="Description"
                  value={item.description}
                  onChange={(e) => updateItem(index, { description: e.target.value })}
                  required
                />
                <input
                  className="rounded-lg border border-ink/15 px-2 py-2 text-sm"
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={item.quantity}
                  onChange={(e) => updateItem(index, { quantity: Number(e.target.value) })}
                />
                <input
                  className="rounded-lg border border-ink/15 px-2 py-2 text-sm"
                  type="number"
                  min="0"
                  step="0.01"
                  value={item.unit_price}
                  onChange={(e) => updateItem(index, { unit_price: Number(e.target.value) })}
                />
                <button
                  type="button"
                  className="text-sm text-rose-700 disabled:opacity-30"
                  disabled={items.length === 1}
                  onClick={() => setItems((prev) => prev.filter((_, i) => i !== index))}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <button type="button" className="mt-2 text-sm text-ink/60 hover:text-ink" onClick={() => setItems((prev) => [...prev, emptyItem()])}>
            + Add line
          </button>
          <p className="mt-3 text-right font-medium">Total {money(total)}</p>
        </div>

        <label className="block text-sm font-medium">
          Notes (shown on invoice)
          <textarea className="mt-1 w-full rounded-lg border border-ink/15 px-3 py-2" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream disabled:opacity-60">
            {saving ? 'Saving…' : 'Save draft'}
          </button>
          <Link to={editing ? `/invoices/${id}` : '/invoices'} className="rounded-lg px-4 py-2 text-sm text-ink/60">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
