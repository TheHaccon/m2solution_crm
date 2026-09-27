import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { api, apiBytes } from '../api'
import { StatusBadge } from '../components/StatusBadge'
import { formatDate, money } from '../lib/format'
import { useTheme } from '../theme/ThemeContext'

type AccountingClient = {
  client_id: number
  client_name: string
  billed_total: string | number
  collected_total: string | number
  outstanding_total: string | number
  invoice_count: number
}

type AccountingInvoice = {
  id: number
  number: string
  client_id: number
  client_name: string
  issue_date: string
  paid_at: string | null
  status: string
  total: string | number
}

type AccountingExpenseCategory = {
  category_id: number
  category_name: string
  total: string | number
  expense_count: number
}

type AccountingExpense = {
  id: number
  spent_on: string
  category_id: number
  category_name: string
  vendor: string | null
  amount: string | number
  receipt_file_id: number | null
}

type AccountingMonth = {
  month: number
  revenue: string | number
  expenses: string | number
}

type Accounting = {
  year: number
  years: number[]
  billed_total: string | number
  collected_total: string | number
  outstanding_total: string | number
  invoice_count: number
  expense_total: string | number
  net_collected: string | number
  by_client: AccountingClient[]
  invoices: AccountingInvoice[]
  by_expense_category: AccountingExpenseCategory[]
  expenses: AccountingExpense[]
  by_month: AccountingMonth[]
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const PIE_COLORS = ['#c4a35a', '#0a1628', '#5b8aa8', '#8b6914', '#3d5a4c', '#a35a5a', '#6b5b8a', '#4a7c59']
const PIE_COLORS_DARK = ['#c4a35a', '#e8d5a3', '#7eb0d6', '#d4a017', '#8fbc8f', '#e07a7a', '#b8a0d4', '#7dce9a']

export function AccountingPage() {
  const { theme } = useTheme()
  const [year, setYear] = useState(new Date().getFullYear())
  const [data, setData] = useState<Accounting | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    setError(null)
    api<Accounting>(`/api/accounting?year=${year}`)
      .then(setData)
      .catch((err: Error) => setError(err.message))
  }, [year])

  async function onExport() {
    setExporting(true)
    setError(null)
    try {
      const { blob } = await apiBytes(`/api/accounting/export?year=${year}`)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `accounting-${year}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExporting(false)
    }
  }

  const years = data?.years?.length ? data.years : [year]
  const dark = theme === 'dark'
  const revenueFill = dark ? '#e8eee8' : '#0a1628'
  const expenseFill = '#c4a35a'
  const tick = dark ? '#c5cdd8' : '#13233d'
  const grid = dark ? 'rgba(232,238,232,0.12)' : 'rgba(10,22,40,0.08)'
  const pieColors = dark ? PIE_COLORS_DARK : PIE_COLORS

  const monthChart = useMemo(
    () =>
      (data?.by_month ?? []).map((row) => ({
        name: MONTHS[row.month - 1],
        Revenue: Number(row.revenue),
        Expenses: Number(row.expenses),
      })),
    [data],
  )
  const hasMonthData = monthChart.some((row) => row.Revenue || row.Expenses)
  const pieData = useMemo(
    () =>
      (data?.by_expense_category ?? []).map((row) => ({
        name: row.category_name,
        value: Number(row.total),
      })),
    [data],
  )
  const pieTotal = pieData.reduce((sum, row) => sum + row.value, 0)

  const cards = data
    ? [
        { label: 'Billed', value: money(data.billed_total), hint: 'Sent or paid, issue date in this year' },
        { label: 'Collected', value: money(data.collected_total), hint: 'Marked paid this year' },
        { label: 'Outstanding', value: money(data.outstanding_total), hint: 'Sent, not paid yet' },
        { label: 'Expenses', value: money(data.expense_total), hint: 'Deductible costs spent this year' },
        { label: 'Net collected', value: money(data.net_collected), hint: 'Collected minus expenses' },
      ]
    : []

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl">Accounting</h1>
          <p className="mt-1 text-ink/55">Year-end billed, collected, and deductible expenses. No tax yet.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
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
          <button
            type="button"
            onClick={() => void onExport()}
            disabled={exporting}
            className="rounded-lg bg-navy px-4 py-2 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-60"
          >
            {exporting ? 'Exporting…' : 'Export CSV'}
          </button>
        </div>
      </div>

      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}
      {!data && !error ? <p className="mt-6 text-ink/50">Loading…</p> : null}

      {data ? (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {cards.map((card) => (
              <div key={card.label} className="rounded-2xl bg-paper p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wider text-ink/45">{card.label}</p>
                <p className="mt-2 font-serif text-3xl tabular-nums">{card.value}</p>
                <p className="mt-1 text-sm text-ink/50">{card.hint}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-2">
            <section className="rounded-2xl bg-paper p-5 shadow-sm">
              <h2 className="font-medium">Revenue vs expenses</h2>
              <p className="mt-0.5 text-xs text-ink/45">Collected (cash in) versus spending, by month.</p>
              {hasMonthData ? (
                <div className="mt-4 h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={monthChart} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid stroke={grid} vertical={false} />
                      <XAxis dataKey="name" tick={{ fill: tick, fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis
                        tick={{ fill: tick, fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(v: number) =>
                          new Intl.NumberFormat('en-CA', { notation: 'compact', currency: 'CAD' }).format(v)
                        }
                      />
                      <Tooltip
                        formatter={(value) => money(Number(value ?? 0))}
                        contentStyle={{ background: dark ? '#122033' : '#fffcf7', border: '1px solid rgba(10,22,40,0.12)' }}
                      />
                      <Legend />
                      <Bar dataKey="Revenue" fill={revenueFill} radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Expenses" fill={expenseFill} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="mt-8 text-center text-sm text-ink/45">No collected revenue or expenses this year.</p>
              )}
            </section>

            <section className="rounded-2xl bg-paper p-5 shadow-sm">
              <h2 className="font-medium">Expenses by category</h2>
              <p className="mt-0.5 text-xs text-ink/45">Where deductible spending went.</p>
              {pieTotal > 0 ? (
                <div className="mt-4 flex flex-wrap items-center gap-4">
                  <div className="h-64 w-64 shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pieData}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={62}
                          outerRadius={95}
                          paddingAngle={2}
                        >
                          {pieData.map((entry, i) => (
                            <Cell key={entry.name} fill={pieColors[i % pieColors.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => money(Number(value ?? 0))} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <ul className="min-w-[12rem] flex-1 space-y-2 text-sm">
                    {pieData.map((row, i) => (
                      <li key={row.name} className="flex items-center justify-between gap-3">
                        <span className="flex items-center gap-2">
                          <span
                            className="inline-block h-2.5 w-2.5 rounded-full"
                            style={{ background: pieColors[i % pieColors.length] }}
                          />
                          {row.name}
                        </span>
                        <span className="tabular-nums text-ink/70">
                          {Math.round((row.value / pieTotal) * 100)}% · {money(row.value)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="mt-8 text-center text-sm text-ink/45">No expenses this year.</p>
              )}
            </section>
          </div>

          <section className="mt-8 overflow-hidden rounded-2xl bg-paper shadow-sm">
            <div className="border-b border-ink/8 px-4 py-3">
              <h2 className="font-medium">By client</h2>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
                <tr>
                  <th className="px-4 py-3 font-medium">Client</th>
                  <th className="px-4 py-3 text-right font-medium">Billed</th>
                  <th className="px-4 py-3 text-right font-medium">Collected</th>
                  <th className="px-4 py-3 text-right font-medium">Outstanding</th>
                  <th className="px-4 py-3 text-right font-medium">Invoices</th>
                </tr>
              </thead>
              <tbody>
                {data.by_client.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-ink/45">
                      No sent or paid invoices this year.
                    </td>
                  </tr>
                ) : (
                  data.by_client.map((row) => (
                    <tr key={row.client_id} className="border-t border-ink/8 hover:bg-ink/5">
                      <td className="px-4 py-3">
                        <Link to={`/clients/${row.client_id}`} className="font-medium hover:underline">
                          {row.client_name}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">{money(row.billed_total)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{money(row.collected_total)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{money(row.outstanding_total)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{row.invoice_count}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>

          <section className="mt-8 overflow-hidden rounded-2xl bg-paper shadow-sm">
            <div className="border-b border-ink/8 px-4 py-3">
              <h2 className="font-medium">By expense category</h2>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
                <tr>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 text-right font-medium">Total</th>
                  <th className="px-4 py-3 text-right font-medium">Count</th>
                </tr>
              </thead>
              <tbody>
                {data.by_expense_category.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-ink/45">
                      No expenses this year.
                    </td>
                  </tr>
                ) : (
                  data.by_expense_category.map((row) => (
                    <tr key={row.category_id} className="border-t border-ink/8">
                      <td className="px-4 py-3">{row.category_name}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{money(row.total)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{row.expense_count}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>

          <section className="mt-8 overflow-hidden rounded-2xl bg-paper shadow-sm">
            <div className="border-b border-ink/8 px-4 py-3">
              <h2 className="font-medium">Invoice register</h2>
              <p className="mt-0.5 text-xs text-ink/45">{data.invoice_count} invoices</p>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
                <tr>
                  <th className="px-4 py-3 font-medium">Number</th>
                  <th className="px-4 py-3 font-medium">Client</th>
                  <th className="px-4 py-3 font-medium">Issue date</th>
                  <th className="px-4 py-3 font-medium">Paid</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 text-right font-medium">Total</th>
                </tr>
              </thead>
              <tbody>
                {data.invoices.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-ink/45">
                      Nothing to report for this year.
                    </td>
                  </tr>
                ) : (
                  data.invoices.map((inv) => (
                    <tr key={inv.id} className="border-t border-ink/8 hover:bg-ink/5">
                      <td className="px-4 py-3">
                        <Link to={`/invoices/${inv.id}`} className="font-medium hover:underline">
                          {inv.number}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-ink/70">{inv.client_name}</td>
                      <td className="px-4 py-3 text-ink/70">{formatDate(inv.issue_date)}</td>
                      <td className="px-4 py-3 text-ink/70">{formatDate(inv.paid_at)}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={inv.status} />
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">{money(inv.total)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>

          <section className="mt-8 overflow-hidden rounded-2xl bg-paper shadow-sm">
            <div className="border-b border-ink/8 px-4 py-3">
              <h2 className="font-medium">Expense register</h2>
              <p className="mt-0.5 text-xs text-ink/45">
                {data.expenses.length} expenses · <Link to="/expenses" className="hover:underline">Manage</Link>
              </p>
            </div>
            <table className="w-full text-sm">
              <thead className="bg-ink/[0.03] text-left text-xs uppercase tracking-wider text-ink/45">
                <tr>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Vendor</th>
                  <th className="px-4 py-3 text-right font-medium">Amount</th>
                </tr>
              </thead>
              <tbody>
                {data.expenses.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-ink/45">
                      No expenses this year.
                    </td>
                  </tr>
                ) : (
                  data.expenses.map((row) => (
                    <tr key={row.id} className="border-t border-ink/8 hover:bg-ink/5">
                      <td className="px-4 py-3">
                        <Link to="/expenses" className="font-medium hover:underline">
                          {formatDate(row.spent_on)}
                        </Link>
                      </td>
                      <td className="px-4 py-3">{row.category_name}</td>
                      <td className="px-4 py-3 text-ink/70">{row.vendor || '—'}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{money(row.amount)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>
        </>
      ) : null}
    </div>
  )
}
