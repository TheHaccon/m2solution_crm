import { money, formatDate } from '../lib/format'
import { StatusBadge } from './StatusBadge'
import type { LineItem } from '../types'

type Props = {
  companyName: string
  companyEmail?: string
  companyAddress?: string
  companyPhone?: string
  clientName: string
  clientEmail?: string | null
  clientAddress?: string | null
  number: string
  status: string
  issueDate: string
  dueDate?: string | null
  notes?: string | null
  lineItems: LineItem[]
  subtotal: string | number
  total: string | number
  showStatus?: boolean
}

export function InvoiceDocument(props: Props) {
  return (
    <article className="invoice-sheet mx-auto w-full max-w-3xl bg-paper p-8 shadow-[0_20px_60px_-24px_rgba(10,22,40,0.45)] sm:p-12">
      <header className="flex flex-wrap items-start justify-between gap-6 border-b border-ink/10 pb-8">
        <div>
          <p className="font-serif text-3xl text-ink">{props.companyName}</p>
          <div className="mt-2 space-y-0.5 text-sm text-ink/70">
            {props.companyAddress ? <p className="whitespace-pre-line">{props.companyAddress}</p> : null}
            {props.companyEmail ? <p>{props.companyEmail}</p> : null}
            {props.companyPhone ? <p>{props.companyPhone}</p> : null}
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gold">Invoice</p>
          <p className="mt-1 font-serif text-2xl text-ink">{props.number}</p>
          {props.showStatus ? (
            <div className="mt-2 flex justify-end">
              <StatusBadge status={props.status} />
            </div>
          ) : null}
        </div>
      </header>

      <div className="mt-8 grid gap-8 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink/50">Bill to</p>
          <p className="mt-1 font-medium text-ink">{props.clientName}</p>
          {props.clientEmail ? <p className="text-sm text-ink/70">{props.clientEmail}</p> : null}
          {props.clientAddress ? <p className="whitespace-pre-line text-sm text-ink/70">{props.clientAddress}</p> : null}
        </div>
        <div className="sm:text-right">
          <p className="text-sm text-ink/70">
            Issue date <span className="font-medium text-ink">{formatDate(props.issueDate)}</span>
          </p>
          {props.dueDate ? (
            <p className="text-sm text-ink/70">
              Due <span className="font-medium text-ink">{formatDate(props.dueDate)}</span>
            </p>
          ) : null}
        </div>
      </div>

      <table className="mt-10 w-full text-sm">
        <thead>
          <tr className="border-b border-ink/15 text-left text-xs uppercase tracking-wider text-ink/50">
            <th className="pb-2 font-medium">Description</th>
            <th className="pb-2 text-right font-medium">Qty</th>
            <th className="pb-2 text-right font-medium">Rate</th>
            <th className="pb-2 text-right font-medium">Amount</th>
          </tr>
        </thead>
        <tbody>
          {props.lineItems.map((item) => (
            <tr key={item.id} className="border-b border-ink/8">
              <td className="py-3 pr-4">{item.description}</td>
              <td className="py-3 text-right tabular-nums">{Number(item.quantity)}</td>
              <td className="py-3 text-right tabular-nums">{money(item.unit_price)}</td>
              <td className="py-3 text-right tabular-nums">{money(item.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-6 flex justify-end">
        <div className="w-56 space-y-1 text-sm">
          <div className="flex justify-between text-ink/70">
            <span>Subtotal</span>
            <span className="tabular-nums">{money(props.subtotal)}</span>
          </div>
          <div className="flex justify-between border-t border-ink/15 pt-2 font-serif text-lg text-ink">
            <span>Total</span>
            <span className="tabular-nums">{money(props.total)}</span>
          </div>
        </div>
      </div>

      {props.notes ? (
        <div className="mt-10 border-t border-ink/10 pt-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-ink/50">Notes</p>
          <p className="mt-2 whitespace-pre-wrap text-sm text-ink/80">{props.notes}</p>
        </div>
      ) : null}

      <p className="mt-12 text-center text-xs text-ink/40">Thank you for your business.</p>
    </article>
  )
}
