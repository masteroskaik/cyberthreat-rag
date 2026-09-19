import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { askQuery, listCves } from '../api/client.js'

const PAGE_SIZE = 15

export default function CvesPage() {
  const [cves, setCves] = useState([])
  const [loadingCves, setLoadingCves] = useState(true)
  const [search, setSearch] = useState('')
  const [severity, setSeverity] = useState('')
  const [kevOnly, setKevOnly] = useState(false)
  const [page, setPage] = useState(0)

  const [selectedCve, setSelectedCve] = useState(null)
  const [generating, setGenerating] = useState(false)

  const navigate = useNavigate()

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

  async function handleGenerateForCve(cve) {
    const q = `Analyse la vulnérabilité ${cve.id} et son impact potentiel.`
    setGenerating(true)
    try {
      await askQuery(q, 'cve', cve.id)
      setSelectedCve(null)
      navigate('/reports')
    } catch (err) {
      alert('Génération impossible, réessaie dans un instant.')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <Layout>
      <h2 style={styles.title}>&gt; vulnerabilities</h2>

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
        <LoadingSpinner label="chargement" />
      ) : (
        <>
          <div className="responsive-table-wrap">
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
                  <tr key={cve.id} className="data-row" style={styles.tr} onClick={() => setSelectedCve(cve)}>
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
          </div>

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

      {selectedCve && (
        <div style={styles.modalOverlay} onClick={() => !generating && setSelectedCve(null)}>
          <div className="glow-border" style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="mono" style={styles.modalTitle}>{selectedCve.id}</span>
                {selectedCve.is_kev && <span style={styles.kevBadge}>ACTIVELY EXPLOITED</span>}
              </div>
              <button
                className="modal-close"
                onClick={() => !generating && setSelectedCve(null)}
                aria-label="Fermer"
              >
                ✕
              </button>
            </div>
            <p style={styles.modalDescription}>{selectedCve.description}</p>
            <div style={styles.modalMeta}>
              <span>severity: <b>{selectedCve.cvss_severity || '—'}</b></span>
              <span>score: <b className="mono">{selectedCve.cvss_score ?? '—'}</b></span>
              <span>published: <b>{selectedCve.published_at?.slice(0, 10) || '—'}</b></span>
            </div>

            {generating ? (
              <LoadingSpinner label="génération du rapport" />
            ) : (
              <button
                className="glow-border"
                style={styles.generateButton}
                onClick={() => handleGenerateForCve(selectedCve)}
              >
                &gt; générer un rapport
              </button>
            )}
          </div>
        </div>
      )}
    </Layout>
  )
}

const styles = {
  title: {
    fontSize: '15px',
    color: 'var(--accent)',
    marginBottom: '20px',
  },
  filterRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
    marginBottom: '16px',
    alignItems: 'center',
  },
  filterInput: {
    flex: '1 1 200px',
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
    minWidth: '520px',
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
    padding: '20px',
  },
  modal: {
    width: '480px',
    maxWidth: '100%',
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
    flexWrap: 'wrap',
    gap: '8px',
  },
  modalTitle: {
    fontSize: '15px',
    color: 'var(--accent)',
  },
  modalDescription: {
    fontSize: '13px',
    lineHeight: 1.6,
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
