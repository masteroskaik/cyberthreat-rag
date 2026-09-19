import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

export default function MarkdownReport({ content }) {
  const html = marked.parse(content || '')
  return (
    <div className="markdown-report" dangerouslySetInnerHTML={{ __html: html }} />
  )
}
