import { useState, useEffect } from 'react'
import Layout from '../components/Layout.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import MarkdownReport from '../components/MarkdownReport.jsx'
import { listReports, downloadReportDocx } from '../api/client.js'

export default function ReportsPage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [openId, setOpenId] = useState(null)
  const [exportingId, setExportingId] = useState(null)

  useEffect(() => {
    listReports()
      .then(setReports)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  async function handleExport(id) {
    setExportingId(id)
    try {
      await downloadReportDocx(id)
    } catch {
      alert("Export impossible, réessaie dans un instant.")
    } finally {
      setExportingId(null)
    }
  }

  return (
    <Layout>
      <h2 style={styles.title}>&gt; reports ({reports.length})</h2>

      {loading ? (
        <LoadingSpinner label="chargement de l'historique" />
      ) : reports.length === 0 ? (
        <p style={styles.empty}>&gt; aucun rapport généré pour l'instant. Va sur "assistant" pour poser une question.</p>
      ) : (
        <div style={styles.list}>
          {reports.map((r) => (
            <div key={r.id} className="glow-border" style={styles.reportCard}>
              <button
                style={styles.reportHeader}
                onClick={() => setOpenId(openId === r.id ? null : r.id)}
              >
                <span style={styles.question}>{r.question}</span>
                <span style={styles.date}>{new Date(r.created_at).toLocaleString()}</span>
              </button>

              {openId === r.id && (
                <div style={styles.reportBody}>
                  <MarkdownReport content={r.answer} />
                  {r.sources?.length > 0 && (
                    <div style={styles.sources}>
                      <span style={styles.sourcesLabel}>sources:</span>
                      {r.sources.map((s, i) => (
                        <span key={i} className="mono" style={styles.sourceTag}>
                          {s.type}:{s.id} [{s.score.toFixed(2)}]
                        </span>
                      ))}
                    </div>
                  )}
                  <button
                    className="glow-border"
                    style={styles.exportButton}
                    onClick={() => handleExport(r.id)}
                    disabled={exportingId === r.id}
                  >
                    {exportingId === r.id ? '...' : '⬇ exporter en .docx'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}

const styles = {
  title: {
    fontSize: '15px',
    color: 'var(--accent)',
    marginBottom: '24px',
  },
  empty: {
    color: 'var(--text-muted)',
    fontSize: '13px',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  reportCard: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    overflow: 'hidden',
  },
  reportHeader: {
    width: '100%',
    background: 'transparent',
    border: 'none',
    padding: '14px 16px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: '4px',
    textAlign: 'left',
    color: 'var(--text)',
  },
  question: {
    fontSize: '13px',
  },
  date: {
    fontSize: '11px',
    color: 'var(--text-muted)',
  },
  reportBody: {
    padding: '0 16px 16px 16px',
    borderTop: '1px solid var(--border)',
  },
  answer: {
    fontSize: '13px',
    lineHeight: 1.7,
    whiteSpace: 'pre-wrap',
    marginTop: '14px',
  },
  sources: {
    marginTop: '14px',
    paddingTop: '14px',
    borderTop: '1px solid var(--border)',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    alignItems: 'center',
  },
  sourcesLabel: {
    fontSize: '11px',
    color: 'var(--text-muted)',
  },
  sourceTag: {
    fontSize: '11px',
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '3px 8px',
    color: 'var(--accent-dim)',
  },
  exportButton: {
    marginTop: '16px',
    background: 'transparent',
    border: '1px solid var(--accent)',
    borderRadius: '2px',
    padding: '9px 16px',
    color: 'var(--accent)',
    fontSize: '12px',
    fontWeight: 600,
  },
}
