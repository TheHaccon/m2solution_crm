import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { api, apiBytes, apiUpload } from '../api'
import { MarkdownBody } from '../markdown/MarkdownBody'
import { useTeam } from '../team/TeamContext'
import type { FileNode } from '../types'

type Space = 'team' | 'personal'
type Dialog =
  | { kind: 'folder' }
  | { kind: 'file' }
  | { kind: 'rename'; node: FileNode }

function isTextFile(node: FileNode): boolean {
  const mime = (node.mime_type || '').toLowerCase()
  if (mime.startsWith('text/') || mime === 'application/json' || mime === 'application/xml' || mime === 'text/yaml') {
    return true
  }
  return /\.(txt|md|markdown|json|csv|yml|yaml|xml|ini|cfg|conf|log|env|html|css|js|ts)$/i.test(node.name)
}

function isMarkdown(node: FileNode): boolean {
  return /\.(md|markdown)$/i.test(node.name) || (node.mime_type || '').toLowerCase() === 'text/markdown'
}

function isImage(node: FileNode): boolean {
  return (node.mime_type || '').startsWith('image/') || /\.(png|jpe?g|gif|webp|svg|bmp)$/i.test(node.name)
}

function isPdf(node: FileNode): boolean {
  return (node.mime_type || '').toLowerCase() === 'application/pdf' || /\.pdf$/i.test(node.name)
}

function formatSize(bytes: number | null): string {
  if (bytes == null) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function childrenOf(nodes: FileNode[], space: Space, parentId: number | null): FileNode[] {
  return nodes
    .filter((n) => n.space === space && n.parent_id === parentId)
    .sort((a, b) => {
      if (a.kind !== b.kind) return a.kind === 'folder' ? -1 : 1
      return a.name.localeCompare(b.name)
    })
}

export function FilesPage() {
  const { teams, teamId } = useTeam()
  const activeTeam = teams.find((t) => t.id === teamId)
  const uploadRef = useRef<HTMLInputElement>(null)

  const [nodes, setNodes] = useState<FileNode[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [space, setSpace] = useState<Space>('team')
  const [folderId, setFolderId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set(['team:root', 'personal:root']))
  const [dialog, setDialog] = useState<Dialog | null>(null)
  const [dialogValue, setDialogValue] = useState('')
  const [previewText, setPreviewText] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)

  const selected = nodes.find((n) => n.id === selectedId) ?? null
  const currentFolder = folderId == null ? null : nodes.find((n) => n.id === folderId) ?? null

  async function reload() {
    const [team, personal] = await Promise.all([
      api<FileNode[]>('/api/files?space=team'),
      api<FileNode[]>('/api/files?space=personal'),
    ])
    setNodes([...team, ...personal])
  }

  useEffect(() => {
    setLoading(true)
    reload()
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [teamId])

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  useEffect(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
    }
    setPreviewText(null)
    setEditing(false)
    setDraft('')
    if (!selected || selected.kind !== 'file') return
    let cancelled = false
    apiBytes(`/api/files/${selected.id}/content`)
      .then(({ blob }) => {
        if (cancelled) return
        if (isTextFile(selected)) {
          return blob.text().then((text) => {
            if (!cancelled) {
              setPreviewText(text)
              setDraft(text)
            }
          })
        }
        if (isImage(selected) || isPdf(selected)) {
          const typed =
            isPdf(selected) && blob.type !== 'application/pdf' ? new Blob([blob], { type: 'application/pdf' }) : blob
          setPreviewUrl(URL.createObjectURL(typed))
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [selectedId, selected?.updated_at])

  function selectRoot(next: Space) {
    setSpace(next)
    setFolderId(null)
    setSelectedId(null)
  }

  function selectNode(node: FileNode) {
    setSpace(node.space)
    setSelectedId(node.id)
    if (node.kind === 'folder') {
      setFolderId(node.id)
      setExpanded((prev) => new Set(prev).add(`${node.space}:${node.id}`))
    } else {
      setFolderId(node.parent_id)
    }
  }

  function toggleFolder(node: FileNode) {
    const key = `${node.space}:${node.id}`
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  async function createFolder(name: string) {
    const created = await api<FileNode>('/api/files/folders', {
      method: 'POST',
      body: JSON.stringify({ name, parent_id: folderId, space }),
    })
    await reload()
    selectNode(created)
  }

  async function createText(name: string) {
    const created = await api<FileNode>('/api/files/text', {
      method: 'POST',
      body: JSON.stringify({ name, parent_id: folderId, space, content: '' }),
    })
    await reload()
    selectNode(created)
    setEditing(true)
  }

  async function upload(file: File) {
    const form = new FormData()
    form.set('space', space)
    if (folderId != null) form.set('parent_id', String(folderId))
    form.set('file', file)
    const created = await apiUpload<FileNode>('/api/files/upload', form)
    await reload()
    selectNode(created)
  }

  async function rename(node: FileNode, name: string) {
    await api(`/api/files/${node.id}`, { method: 'PATCH', body: JSON.stringify({ name }) })
    await reload()
  }

  async function remove(node: FileNode) {
    const label = node.kind === 'folder' ? `Delete folder “${node.name}” and everything inside?` : `Delete “${node.name}”?`
    if (!confirm(label)) return
    try {
      await api(`/api/files/${node.id}`, { method: 'DELETE' })
      if (selectedId === node.id) setSelectedId(null)
      if (folderId === node.id) setFolderId(node.parent_id)
      await reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  async function download(node: FileNode) {
    const { blob } = await apiBytes(`/api/files/${node.id}/content?download=1`)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = node.name
    a.click()
    URL.revokeObjectURL(url)
  }

  async function saveText() {
    if (!selected || selected.kind !== 'file') return
    setSaving(true)
    setError(null)
    try {
      const updated = await api<FileNode>(`/api/files/${selected.id}/content`, {
        method: 'PUT',
        body: JSON.stringify({ content: draft }),
      })
      setPreviewText(draft)
      setEditing(false)
      setNodes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  async function onDialogSubmit(e: FormEvent) {
    e.preventDefault()
    const name = dialogValue.trim()
    if (!name || !dialog) return
    setError(null)
    try {
      if (dialog.kind === 'folder') await createFolder(name)
      else if (dialog.kind === 'file') await createText(name)
      else await rename(dialog.node, name)
      setDialog(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    }
  }

  const locationLabel = useMemo(() => {
    const root = space === 'team' ? activeTeam?.name ?? 'Team' : 'Personal'
    if (!currentFolder) return root
    const parts = [currentFolder.name]
    let parent = currentFolder.parent_id
    while (parent) {
      const next = nodes.find((n) => n.id === parent)
      if (!next) break
      parts.unshift(next.name)
      parent = next.parent_id
    }
    return `${root} / ${parts.join(' / ')}`
  }, [space, activeTeam, currentFolder, nodes])

  const btn =
    'rounded-lg border border-ink/15 bg-paper px-3 py-1.5 text-sm disabled:opacity-40 hover:bg-ink/5'
  const btnPrimary = 'rounded-lg bg-navy px-3 py-1.5 text-sm font-medium text-cream hover:bg-navy-2 disabled:opacity-40'

  return (
    <div className="flex h-[calc(100svh-4rem)] min-h-[28rem] flex-col">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl">Files</h1>
          <p className="mt-1 text-sm text-ink/55">{locationLabel}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className={btn} onClick={() => { setDialogValue(''); setDialog({ kind: 'folder' }) }}>
            New folder
          </button>
          <button type="button" className={btn} onClick={() => { setDialogValue('config.md'); setDialog({ kind: 'file' }) }}>
            New file
          </button>
          <button type="button" className={btnPrimary} onClick={() => uploadRef.current?.click()}>
            Upload
          </button>
          <input
            ref={uploadRef}
            type="file"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              e.target.value = ''
              if (!file) return
              setError(null)
              upload(file).catch((err: Error) => setError(err.message))
            }}
          />
        </div>
      </div>
      {error ? <p className="mt-3 text-rose-700">{error}</p> : null}

      <div className="mt-4 flex min-h-0 flex-1 overflow-hidden rounded-2xl bg-paper shadow-sm">
        <aside className="w-64 shrink-0 overflow-y-auto border-r border-ink/10 p-2 text-sm">
          {loading ? <p className="px-2 py-4 text-ink/45">Loading…</p> : null}
          <RootRow
            label={activeTeam?.name ?? 'Team'}
            hint="Shared"
            active={space === 'team' && selectedId == null && folderId == null}
            onClick={() => selectRoot('team')}
          />
          <TreeList
            nodes={nodes}
            space="team"
            parentId={null}
            selectedId={selectedId}
            expanded={expanded}
            onSelect={selectNode}
            onToggle={toggleFolder}
          />
          <RootRow
            label="Personal"
            hint="Only you"
            active={space === 'personal' && selectedId == null && folderId == null}
            onClick={() => selectRoot('personal')}
          />
          <TreeList
            nodes={nodes}
            space="personal"
            parentId={null}
            selectedId={selectedId}
            expanded={expanded}
            onSelect={selectNode}
            onToggle={toggleFolder}
          />
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          {selected ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-ink/10 px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate font-medium">{selected.name}</p>
                  <p className="text-xs text-ink/45">
                    {selected.kind === 'folder' ? 'Folder' : selected.mime_type || 'File'}
                    {selected.kind === 'file' ? ` · ${formatSize(selected.size_bytes)}` : null}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className={btn}
                    onClick={() => {
                      setDialogValue(selected.name)
                      setDialog({ kind: 'rename', node: selected })
                    }}
                  >
                    Rename
                  </button>
                  {selected.kind === 'file' ? (
                    <button type="button" className={btn} onClick={() => download(selected).catch((err: Error) => setError(err.message))}>
                      Download
                    </button>
                  ) : null}
                  {selected.kind === 'file' && isTextFile(selected) ? (
                    editing ? (
                      <>
                        <button type="button" className={btn} onClick={() => { setEditing(false); setDraft(previewText ?? '') }}>
                          Cancel
                        </button>
                        <button type="button" className={btnPrimary} disabled={saving} onClick={() => void saveText()}>
                          {saving ? 'Saving…' : 'Save'}
                        </button>
                      </>
                    ) : (
                      <button type="button" className={btn} onClick={() => setEditing(true)}>
                        Edit
                      </button>
                    )
                  ) : null}
                  <button type="button" className="rounded-lg px-3 py-1.5 text-sm text-rose-700 hover:bg-ink/5" onClick={() => void remove(selected)}>
                    Delete
                  </button>
                </div>
              </div>
              <div
                className={`min-h-0 flex-1 p-5 ${
                  selected.kind === 'file' && isPdf(selected) && previewUrl && !editing ? 'overflow-hidden' : 'overflow-auto'
                }`}
              >
                {selected.kind === 'folder' ? (
                  <FolderContents
                    items={childrenOf(nodes, selected.space, selected.id)}
                    onOpen={selectNode}
                  />
                ) : editing ? (
                  <textarea
                    className="h-full min-h-[16rem] w-full rounded-lg border border-ink/15 bg-paper p-3 font-mono text-sm outline-none focus:border-gold"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                  />
                ) : isMarkdown(selected) && previewText != null ? (
                  previewText ? <MarkdownBody text={previewText} /> : <p className="text-ink/45">Empty file.</p>
                ) : isTextFile(selected) && previewText != null ? (
                  <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-navy p-3 font-mono text-sm text-cream">
                    {previewText || 'Empty file.'}
                  </pre>
                ) : isPdf(selected) && previewUrl ? (
                  <iframe title={selected.name} src={previewUrl} className="h-full min-h-[28rem] w-full rounded-lg bg-paper" />
                ) : previewUrl ? (
                  <img src={previewUrl} alt={selected.name} className="max-h-full max-w-full rounded-lg" />
                ) : (
                  <p className="text-ink/55">
                    Preview is not available for this type.{' '}
                    <button type="button" className="underline" onClick={() => download(selected).catch((err: Error) => setError(err.message))}>
                      Download
                    </button>
                  </p>
                )}
              </div>
            </>
          ) : (
            <FolderContents items={childrenOf(nodes, space, folderId)} onOpen={selectNode} empty="Select a folder or upload a file." />
          )}
        </section>
      </div>

      {dialog ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-navy/50 p-4">
          <form className="w-full max-w-sm rounded-2xl bg-paper p-5 shadow-lg" onSubmit={(e) => void onDialogSubmit(e)}>
            <h2 className="font-serif text-xl">
              {dialog.kind === 'folder' ? 'New folder' : dialog.kind === 'file' ? 'New file' : 'Rename'}
            </h2>
            <label className="mt-4 block text-sm text-ink/70">
              Name
              <input
                autoFocus
                className="mt-1 w-full rounded-lg border border-ink/15 bg-paper px-3 py-2 outline-none focus:border-gold"
                value={dialogValue}
                onChange={(e) => setDialogValue(e.target.value)}
                placeholder={dialog.kind === 'file' ? 'notes.md' : 'Name'}
              />
            </label>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className={btn} onClick={() => setDialog(null)}>
                Cancel
              </button>
              <button type="submit" className={btnPrimary} disabled={!dialogValue.trim()}>
                {dialog.kind === 'rename' ? 'Rename' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  )
}

function RootRow({
  label,
  hint,
  active,
  onClick,
}: {
  label: string
  hint: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`mt-2 flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left first:mt-0 ${
        active ? 'bg-ink/10 font-medium' : 'hover:bg-ink/5'
      }`}
    >
      <span className="truncate">{label}</span>
      <span className="text-[10px] uppercase tracking-wider text-ink/40">{hint}</span>
    </button>
  )
}

function TreeList({
  nodes,
  space,
  parentId,
  selectedId,
  expanded,
  onSelect,
  onToggle,
}: {
  nodes: FileNode[]
  space: Space
  parentId: number | null
  selectedId: number | null
  expanded: Set<string>
  onSelect: (node: FileNode) => void
  onToggle: (node: FileNode) => void
}) {
  const items = childrenOf(nodes, space, parentId)
  const pad = parentId == null ? 'pl-2' : 'pl-5'
  return (
    <ul className={pad}>
      {items.map((node) => {
        const open = expanded.has(`${node.space}:${node.id}`)
        const active = selectedId === node.id
        return (
          <li key={node.id}>
            <div className={`flex items-center rounded-lg ${active ? 'bg-ink/10' : 'hover:bg-ink/5'}`}>
              {node.kind === 'folder' ? (
                <button
                  type="button"
                  className="px-1 text-ink/40"
                  aria-label={open ? 'Collapse' : 'Expand'}
                  onClick={() => onToggle(node)}
                >
                  {open ? '▾' : '▸'}
                </button>
              ) : (
                <span className="w-5" />
              )}
              <button type="button" className="min-w-0 flex-1 truncate py-1 pr-2 text-left" onClick={() => onSelect(node)}>
                <span className={node.kind === 'folder' ? 'font-medium' : ''}>{node.name}</span>
              </button>
            </div>
            {node.kind === 'folder' && open ? (
              <TreeList
                nodes={nodes}
                space={space}
                parentId={node.id}
                selectedId={selectedId}
                expanded={expanded}
                onSelect={onSelect}
                onToggle={onToggle}
              />
            ) : null}
          </li>
        )
      })}
    </ul>
  )
}

function FolderContents({
  items,
  onOpen,
  empty = 'This folder is empty.',
}: {
  items: FileNode[]
  onOpen: (node: FileNode) => void
  empty?: string
}) {
  if (items.length === 0) {
    return <p className="p-5 text-ink/45">{empty}</p>
  }
  return (
    <ul className="p-2">
      {items.map((node) => (
        <li key={node.id}>
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm hover:bg-ink/5"
            onClick={() => onOpen(node)}
          >
            <span className={node.kind === 'folder' ? 'font-medium' : ''}>{node.name}</span>
            <span className="text-xs text-ink/40">{node.kind === 'file' ? formatSize(node.size_bytes) : ''}</span>
          </button>
        </li>
      ))}
    </ul>
  )
}
