import { useEffect, useState, type FormEvent } from 'react'

import { api, apiBytes, apiUpload } from '../api'
import { formatDate, money, todayISO } from '../lib/format'

type Category = { id: number; name: string }
type Expense = {
  id: number
  category_id: number
  category_name: string
  amount: string | number
  spent_on: string
  vendor: string | null
  notes: string | null
  receipt_file_id: number | null
  receipt_name: string | null
  recurrence_id: number | null
}
type Recurrence = {
  id: number
  category_id: number
  category_name: string
  amount: string | number
  vendor: string | null
  next_on: string
  active: boolean
}

export function ExpensesPage() {
  const [year, setYear] = useState(new Date().getFullYear())
  const [categoryFilter, setCategoryFilter] = useState('')
  const [categories, setCategories] = useState<Category[]>([])
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [recurrences, setRecurrences] = useState<Recurrence[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const [spentOn, setSpentOn] = useState(todayISO())
  const [amount, setAmount] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [vendor, setVendor] = useState('')
  const [notes, setNotes] = useState('')
  const [repeatMonthly, setRepeatMonthly] = useState(false)
  const [receipt, setReceipt] = useState<File | null>(null)
  const [newCategory, setNewCategory] = useState('')

  const years = [year, year - 1, year - 2, year - 3]

  async function reload() {
    const qs = new URLSearchParams({ year: String(year) })
    if (categoryFilter) qs.set('category_id', categoryFilter)
    const [cats, rows, recs] = await Promise.all([
      api<Category[]>('/api/expense-categories'),
      api<Expense[]>(`/api/expenses?${qs}`),
      api<Recurrence[]>('/api/expense-recurrences'),
    ])
    setCategories(cats)
    setExpenses(rows)
    setRecurrences(recs)
    if (!categoryId && cats[0]) setCategoryId(String(cats[0].id))
  }

  useEffect(() => {
    setError(null)
    reload().catch((err: Error) => setError(err.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload on filters only
  }, [year, categoryFilter])

  function resetForm() {
    setEditingId(null)
    setSpentOn(todayISO())
    setAmount('')
    setVendor('')
    setNotes('')
    setRepeatMonthly(false)
    setReceipt(null)
    setNewCategory('')
    if (categories[0]) setCategoryId(String(categories[0].id))
  }

  function openCreate() {
    resetForm()
    setShowForm(true)
  }

  function openEdit(row: Expense) {
    setEditingId(row.id)
    setSpentOn(row.spent_on)
    setAmount(String(row.amount))
    setCategoryId(String(row.category_id))
    setVendor(row.vendor ?? '')
    setNotes(row.notes ?? '')
    setRepeatMonthly(false)
    setReceipt(null)
    setShowForm(true)
  }

  async function addCategory() {
    const name = newCategory.trim()
    if (!name) return
    const created = await api<Category>('/api/expense-categories', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
    setCategories((prev) => [...prev, created].sort((a, b) => a.name.localeCompare(b.name)))
    setCategoryId(String(created.id))
    setNewCategory('')
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const body = {
        category_id: Number(categoryId),
        amount,
        spent_on: spentOn,
        vendor: vendor.trim() || null,
        notes: notes.trim() || null,
        repeat_monthly: editingId ? false : repeatMonthly,
      }
      let saved: Expense
      if (editingId) {
        saved = await api<Expense>(`/api/expenses/${editingId}`, { method: 'PATCH', body: JSON.stringify(body) })
      } else {
        saved = await api<Expense>('/api/expenses', { method: 'POST', body: JSON.stringify(body) })
      }
      if (receipt) {
        const form = new FormData()
        form.append('file', receipt)
        saved = await apiUpload<Expense>(`/api/expenses/${saved.id}/receipt`, form)
      }
      setShowForm(false)
      resetForm()
      await reload()
      void saved
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(id: number) {
    if (!window.confirm('Delete this expense?')) return
    setError(null)
    try {
      await api(`/api/expenses/${id}`, { method: 'DELETE' })
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  async function downloadReceipt(row: Expense) {
    if (!row.receipt_file_id) return
    const { blob } = await apiBytes(`/api/files/${row.receipt_file_id}/content?download=1`)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.receipt_name || 'receipt'
    a.click()
    URL.revokeObjectURL(url)
  }

  async function toggleRecurrence(row: Recurrence) {
    setError(null)
    try {
      await api(`/api/expense-recurrences/${row.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ active: !row.active }),
      })
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    }
  }

  async function deleteRecurrence(id: number) {
    if (!window.confirm('Stop this recurring expense? Existing rows stay in the register.')) return
    setError(null)
    try {
      await api(`/api/expense-recurrences/${id}`, { method: 'DELETE' })
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">Expenses</h1>
          <p className="mt-1 text-ink/55">Your deductible costs — gas, purchases, auto, subscriptions. No tax yet.</p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream hover:bg-navy-2"
        >
          New expense
        </button>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <label className="text-sm text-ink/60">
          Year
          <select
            className="ml-2 rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm outline-none focus:border-gold"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-ink/60">
          Category
          <select
            className="ml-2 rounded-lg border border-ink/15 bg-paper px-3 py-2 text-sm outline-none focus:border-gold"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}

      {showForm ? (
        <form onSubmit={(e) => void onSubmit(e)} className="mt-6 space-y-3 rounded-2xl bg-paper p-5 shadow-sm">
          <h2 className="font-medium">{editingId ? 'Edit expense' : 'New expense'}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm">
              Date
              <input
                type="date"
                required
                value={spentOn}
                onChange={(e) => setSpentOn(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
              />
            </label>
            <label className="text-sm">
              Amount (CAD)
              <input
                type="number"
                required
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
              />
            </label>
            <label className="text-sm">
              Category
              <select
                required
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              Vendor
              <input
                value={vendor}
                onChange={(e) => setVendor(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
              />
            </label>
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-sm">
              New category
              <input
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
              />
            </label>
            <button
              type="button"
              onClick={() => void addCategory().catch((err: Error) => setError(err.message))}
              className="rounded-lg bg-ink/8 px-3 py-2 text-sm"
            >
              Add
            </button>
          </div>
          <label className="block text-sm">
            Notes
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
            />
          </label>
          <label className="block text-sm">
            Receipt
            <input
              type="file"
              onChange={(e) => setReceipt(e.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm"
            />
          </label>
          {!editingId ? (
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={repeatMonthly} onChange={(e) => setRepeatMonthly(e.target.checked)} />
              Repeat monthly
            </label>
          ) : null}
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-60"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false)
                resetForm()
              }}
              className="rounded-lg px-4 py-2 text-sm text-ink/70"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : null}

      <section className="mt-8 overflow-hidden rounded-2xl bg-paper shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
            <tr>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="px-4 py-3 font-medium">Vendor</th>
              <th className="px-4 py-3 text-right font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Receipt</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {expenses.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink/45">
                  No expenses this year.
                </td>
              </tr>
            ) : (
              expenses.map((row) => (
                <tr key={row.id} className="border-t border-ink/8 hover:bg-ink/5">
                  <td className="px-4 py-3">{formatDate(row.spent_on)}</td>
                  <td className="px-4 py-3">{row.category_name}</td>
                  <td className="px-4 py-3 text-ink/70">{row.vendor || '—'}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{money(row.amount)}</td>
                  <td className="px-4 py-3">
                    {row.receipt_file_id ? (
                      <button type="button" className="hover:underline" onClick={() => void downloadReceipt(row)}>
                        {row.receipt_name || 'Receipt'}
                      </button>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="mr-3 text-ink/60 hover:underline" onClick={() => openEdit(row)}>
                      Edit
                    </button>
                    <button type="button" className="text-rose-700 hover:underline" onClick={() => void onDelete(row.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="mt-8 overflow-hidden rounded-2xl bg-paper shadow-sm">
        <div className="border-b border-ink/8 px-4 py-3">
          <h2 className="font-medium">Recurring</h2>
          <p className="mt-0.5 text-xs text-ink/45">Monthly rows are created when you open Expenses or Accounting.</p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
            <tr>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="px-4 py-3 font-medium">Vendor</th>
              <th className="px-4 py-3 text-right font-medium">Amount</th>
              <th className="px-4 py-3 font-medium">Next</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {recurrences.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink/45">
                  No recurring expenses. Check “Repeat monthly” when adding one.
                </td>
              </tr>
            ) : (
              recurrences.map((row) => (
                <tr key={row.id} className="border-t border-ink/8">
                  <td className="px-4 py-3">{row.category_name}</td>
                  <td className="px-4 py-3 text-ink/70">{row.vendor || '—'}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{money(row.amount)}</td>
                  <td className="px-4 py-3">{formatDate(row.next_on)}</td>
                  <td className="px-4 py-3">{row.active ? 'Active' : 'Paused'}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      className="mr-3 text-ink/60 hover:underline"
                      onClick={() => void toggleRecurrence(row)}
                    >
                      {row.active ? 'Pause' : 'Resume'}
                    </button>
                    <button
                      type="button"
                      className="text-rose-700 hover:underline"
                      onClick={() => void deleteRecurrence(row.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
