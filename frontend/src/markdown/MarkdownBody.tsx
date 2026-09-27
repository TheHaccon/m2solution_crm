import type { Components } from 'react-markdown'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const components: Components = {
  h1: ({ children }) => <h1 className="mt-6 font-serif text-2xl first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="mt-5 font-serif text-xl first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="mt-4 font-medium first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="my-2">{children}</p>,
  ul: ({ children }) => <ul className="my-2 ml-5 list-disc space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 ml-5 list-decimal space-y-1">{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-gold/60 pl-3 text-ink/70">{children}</blockquote>
  ),
  a: ({ href, children }) => (
    <a href={href} className="text-gold underline underline-offset-2" target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
  hr: () => <hr className="my-4 border-ink/15" />,
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => <th className="border border-ink/15 bg-ink/5 px-2 py-1 text-left font-medium">{children}</th>,
  td: ({ children }) => <td className="border border-ink/15 px-2 py-1">{children}</td>,
  del: ({ children }) => <del className="text-ink/55">{children}</del>,
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-lg bg-navy p-3 text-sm leading-relaxed text-cream">{children}</pre>
  ),
  code: ({ className, children }) => {
    const isBlock = Boolean(className?.includes('language-')) || String(children).includes('\n')
    if (isBlock) {
      return <code className="font-mono text-[0.85em] text-cream">{children}</code>
    }
    return <code className="rounded bg-navy/15 px-1 py-px font-mono text-[0.85em]">{children}</code>
  },
}

export function MarkdownBody({ text }: { text: string }) {
  return (
    <Markdown remarkPlugins={[remarkGfm]} components={components}>
      {text}
    </Markdown>
  )
}
