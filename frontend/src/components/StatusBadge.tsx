const styles: Record<string, string> = {
  draft: 'bg-slate-200 text-slate-700',
  sent: 'bg-sky-100 text-sky-800',
  paid: 'bg-emerald-100 text-emerald-800',
  void: 'bg-rose-100 text-rose-800',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${styles[status] ?? 'bg-slate-100 text-slate-600'}`}>
      {status}
    </span>
  )
}
