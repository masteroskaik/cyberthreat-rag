import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { askQuery, listCves, getStats, logout } from '../api/client.js'

const PAGE_SIZE = 15

export default function DashboardPage() {
  const [question, setQuestion] = useState('')
  const [report, setReport] = useState(null)
  const [loadingQuery, setLoadingQuery] = useState(false)
  const [queryError, setQueryError] = useState('')

  const [stats, setStats] = useState(null)

  const [cves, setCves] = useState([])
  const [loadingCves, setLoadingCves] = useState(true)
  const [search, setSearch] = useState('')
  const [severity, setSeverity] = useState('')
  const [kevOnly, setKevOnly] = useState(false)
  const [page, setPage] = useState(0)

  const [selectedCve, setSelectedCve] = useState(null)

  const navigate = useNavigate()

  useEffect(() => {
    getStats().then(setStats).catch(() => {})
  }, [])

  useEffect(() => {
    setLoadingCves(true)
    listCves(PAGE_SIZE, page * PAGE_SIZE, severity || null)
      .then(setCves)
      .catch(() => {})
      .finally(() => setLoadingCves(false))
  }, [page, severity])

  const filteredCves = cves.filter((c) => {
    if (kevOnly && !c.is_kev) return false
    if (search && !c.id.toLowerCase().includes(search.toLowerCase()) &&
        !c.description.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  async function runQuery(text) {
    if (!text.trim()) return
    setLoadingQuery(true)
    setQueryError('')
    setReport(null)
    try {
      const data = await askQuery(text)
      setReport(data)
    } catch (err) {
      setQueryError('> ERROR — génération impossible, réessaie dans un instant')
    } finally {
      setLoadingQuery(false)
    }
  }

  function handleAsk(e) {
    e.preventDefault()
    runQuery(question)
  }

  function handleGenerateForCve(cve) {
    const q = `Analyse la vulnérabilité ${cve.id} et son impact potentiel.`
    setQuestion(q)
    setSelectedCve(null)
    runQuery(q)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div style={styles.layout}>
      <aside style={styles.sidebar}>
        <div style={styles.brand}>
          <span style={{ color: 'var(--accent)' }}>&gt;_</span>
          <span style={styles.brandName}>CYBERTHREAT_RAG</span>
        </div>
        <nav style={styles.nav}>
          <span style={styles.navItemActive}>dashboard</span>
        </nav>
        <button className="glow-border" style={styles.logoutButton} onClick={handleLogout}>
          &gt; logout
        </button>
      </aside>

      <main style={styles.main}>
        {stats && (
          <section style={styles.statsRow}>
            <StatCard label="cves_indexées" value={stats.total_cves} />
            <StatCard label="kev_confirmées" value={stats.total_kev} accent="critical" />
            <StatCard label="techniques_att&ck" value={stats.total_techniques} />
          </section>
        )}

        <section>
          <h2 style={styles.sectionTitle}>&gt; query</h2>
          <form onSubmit={handleAsk} style={styles.queryForm}>
            <input
              className="glow-border"
              style={styles.queryInput}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="quelles techniques att&ck sont liées à l'exploitation de vulnérabilités ?"
            />
            <button className="glow-border" style={styles.queryButton} type="submit" disabled={loadingQuery}>
              {loadingQuery ? '...' : 'run'}
            </button>
          </form>

          {queryError && <p style={styles.error}>{queryError}</p>}

          {report && (
            <div className="glow-border" style={styles.reportBox}>
              <p style={styles.reportText}>{report.answer}</p>
              {report.sources?.length > 0 && (
                <div style={styles.sources}>
                  <span style={styles.sourcesLabel}>sources:</span>
                  {report.sources.map((s, i) => (
                    <span key={i} className="mono" style={styles.sourceTag}>
                      {s.type}:{s.id} [{s.score.toFixed(2)}]
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>

        <section style={{ marginTop: '36px' }}>
          <h2 style={styles.sectionTitle}>&gt; vulnerabilities</h2>

          <div style={styles.filterRow}>
            <input
              className="glow-border"
              style={styles.filterInput}
              placeholder="filtrer par ID ou mot-clé..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className="glow-border"
              style={styles.filterSelect}
              value={severity}
              onChange={(e) => { setSeverity(e.target.value); setPage(0) }}
            >
              <option value="">toutes sévérités</option>
              <option value="CRITICAL">critical</option>
              <option value="HIGH">high</option>
              <option value="MEDIUM">medium</option>
              <option value="LOW">low</option>
            </select>
            <label style={styles.checkboxLabel}>
              <input type="checkbox" checked={kevOnly} onChange={(e) => setKevOnly(e.target.checked)} />
              kev uniquement
            </label>
          </div>

          {loadingCves ? (
            <p style={{ color: 'var(--text-muted)' }}>&gt; loading...</p>
          ) : (
            <>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>cve_id</th>
                    <th style={styles.th}>severity</th>
                    <th style={styles.th}>score</th>
                    <th style={styles.th}>kev</th>
                    <th style={styles.th}>published</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCves.map((cve) => (
                    <tr key={cve.id} style={styles.tr} onClick={() => setSelectedCve(cve)}>
                      <td className="mono" style={styles.td}>{cve.id}</td>
                      <td style={styles.td}>{cve.cvss_severity || '—'}</td>
                      <td className="mono" style={styles.td}>{cve.cvss_score ?? '—'}</td>
                      <td style={styles.td}>
                        {cve.is_kev ? <span style={styles.kevBadge}>ACTIVE</span> : '—'}
                      </td>
                      <td style={styles.td}>{cve.published_at?.slice(0, 10) || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={styles.pagination}>
                <button
                  className="glow-border"
                  style={styles.pageButton}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  &lt; prev
                </button>
                <span style={styles.pageLabel}>page {page + 1}</span>
                <button
                  className="glow-border"
                  style={styles.pageButton}
                  onClick={() => setPage((p) => p + 1)}
                  disabled={cves.length < PAGE_SIZE}
                >
                  next &gt;
                </button>
              </div>
            </>
          )}
        </section>
      </main>

      {selectedCve && (
        <div style={styles.modalOverlay} onClick={() => setSelectedCve(null)}>
          <div className="glow-border" style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <span className="mono" style={styles.modalTitle}>{selectedCve.id}</span>
              {selectedCve.is_kev && <span style={styles.kevBadge}>ACTIVELY EXPLOITED</span>}
            </div>
            <p style={styles.modalDescription}>{selectedCve.description}</p>
            <div style={styles.modalMeta}>
              <span>severity: <b>{selectedCve.cvss_severity || '—'}</b></span>
              <span>score: <b className="mono">{selectedCve.cvss_score ?? '—'}</b></span>
              <span>published: <b>{selectedCve.published_at?.slice(0, 10) || '—'}</b></span>
            </div>
            <button
              className="glow-border"
              style={styles.generateButton}
              onClick={() => handleGenerateForCve(selectedCve)}
            >
              &gt; générer un rapport
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, accent }) {
  return (
    <div className="glow-border" style={styles.statCard}>
      <span className="mono" style={{
        ...styles.statValue,
        color: accent === 'critical' ? 'var(--critical)' : 'var(--accent)',
      }}>
        {value}
      </span>
      <span style={styles.statLabel}>{label}</span>
    </div>
  )
}

const styles = {
  layout: {
    display: 'flex',
    minHeight: '100vh',
  },
  sidebar: {
    width: '220px',
    borderRight: '1px solid var(--border)',
    padding: '24px 20px',
    display: 'flex',
    flexDirection: 'column',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '32px',
  },
  brandName: {
    fontSize: '13px',
    fontWeight: 600,
    letterSpacing: '0.03em',
  },
  nav: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    flex: 1,
  },
  navItemActive: {
    color: 'var(--accent)',
    padding: '8px 10px',
    fontSize: '13px',
  },
  logoutButton: {
    background: 'transparent',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '9px',
    color: 'var(--text-muted)',
    fontSize: '12px',
  },
  main: {
    flex: 1,
    padding: '32px 40px',
    maxWidth: '960px',
  },
  statsRow: {
    display: 'flex',
    gap: '16px',
    marginBottom: '36px',
  },
  statCard: {
    flex: 1,
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '16px 18px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  statValue: {
    fontSize: '24px',
    fontWeight: 700,
  },
  statLabel: {
    fontSize: '11px',
    color: 'var(--text-muted)',
  },
  sectionTitle: {
    fontSize: '14px',
    marginBottom: '14px',
    color: 'var(--accent)',
  },
  queryForm: {
    display: 'flex',
    gap: '10px',
  },
  queryInput: {
    flex: 1,
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '11px 14px',
    color: 'var(--text)',
    fontSize: '13px',
  },
  queryButton: {
    background: 'transparent',
    border: '1px solid var(--accent)',
    borderRadius: '2px',
    padding: '11px 20px',
    color: 'var(--accent)',
    fontWeight: 600,
    fontSize: '13px',
    whiteSpace: 'nowrap',
  },
  error: {
    color: 'var(--critical)',
    fontSize: '12px',
    marginTop: '12px',
  },
  reportBox: {
    marginTop: '20px',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '20px',
  },
  reportText: {
    fontSize: '13px',
    lineHeight: 1.7,
    whiteSpace: 'pre-wrap',
    margin: 0,
  },
  sources: {
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid var(--border)',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    alignItems: 'center',
  },
  sourcesLabel: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    marginRight: '4px',
  },
  sourceTag: {
    fontSize: '11px',
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '3px 8px',
    color: 'var(--accent-dim)',
  },
  filterRow: {
    display: 'flex',
    gap: '10px',
    marginBottom: '16px',
    alignItems: 'center',
  },
  filterInput: {
    flex: 1,
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '9px 12px',
    color: 'var(--text)',
    fontSize: '12px',
  },
  filterSelect: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '9px 12px',
    color: 'var(--text)',
    fontSize: '12px',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    color: 'var(--text-muted)',
    whiteSpace: 'nowrap',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '12px',
  },
  th: {
    textAlign: 'left',
    padding: '8px 12px',
    color: 'var(--text-muted)',
    fontWeight: 500,
    borderBottom: '1px solid var(--border)',
  },
  tr: {
    cursor: 'pointer',
  },
  td: {
    padding: '10px 12px',
    borderBottom: '1px solid var(--border)',
  },
  kevBadge: {
    color: 'var(--critical)',
    fontSize: '11px',
    fontWeight: 600,
    border: '1px solid var(--critical)',
    borderRadius: '2px',
    padding: '2px 6px',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '16px',
    marginTop: '20px',
  },
  pageButton: {
    background: 'transparent',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '7px 14px',
    color: 'var(--text)',
    fontSize: '12px',
  },
  pageLabel: {
    fontSize: '12px',
    color: 'var(--text-muted)',
  },
  modalOverlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  modal: {
    width: '480px',
    maxWidth: '90vw',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '24px',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '14px',
  },
  modalTitle: {
    fontSize: '15px',
    color: 'var(--accent)',
  },
  modalDescription: {
    fontSize: '13px',
    lineHeight: 1.6,
    color: 'var(--text)',
    marginBottom: '16px',
  },
  modalMeta: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    fontSize: '12px',
    color: 'var(--text-muted)',
    marginBottom: '20px',
  },
  generateButton: {
    width: '100%',
    background: 'transparent',
    border: '1px solid var(--accent)',
    borderRadius: '2px',
    padding: '11px',
    color: 'var(--accent)',
    fontWeight: 600,
    fontSize: '13px',
  },
}
