import { useState, useEffect } from 'react'
import Layout from '../components/Layout.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { listTechniques } from '../api/client.js'

export default function TechniquesPage() {
  const [techniques, setTechniques] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    setLoading(true)
    const timeout = setTimeout(() => {
      listTechniques(search, 100, 0)
        .then(setTechniques)
        .catch(() => {})
        .finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(timeout)
  }, [search])

  return (
    <Layout>
      <h2 style={styles.title}>&gt; techniques att&amp;ck</h2>

      <input
        className="glow-border"
        style={styles.searchInput}
        placeholder="rechercher par ID, nom ou mot-clé..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {loading ? (
        <LoadingSpinner label="chargement" />
      ) : (
        <div className="responsive-table-wrap">
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>id</th>
                <th style={styles.th}>name</th>
                <th style={styles.th}>tactics</th>
                <th style={styles.th}>platforms</th>
              </tr>
            </thead>
            <tbody>
              {techniques.map((t) => (
                <tr key={t.id} className="data-row" style={styles.tr} onClick={() => setSelected(t)}>
                  <td className="mono" style={styles.td}>{t.id}</td>
                  <td style={styles.td}>{t.name}</td>
                  <td style={styles.td}>{t.tactics.slice(0, 2).join(', ') || '—'}</td>
                  <td style={styles.td}>{t.platforms.slice(0, 2).join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {techniques.length === 0 && (
            <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '16px' }}>
              &gt; aucune technique trouvée
            </p>
          )}
        </div>
      )}

      {selected && (
        <div style={styles.modalOverlay} onClick={() => setSelected(null)}>
          <div className="glow-border" style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span className="mono" style={styles.modalTitle}>{selected.id}</span>
                <span style={styles.modalName}>{selected.name}</span>
              </div>
              <button
                className="modal-close"
                onClick={() => setSelected(null)}
                aria-label="Fermer"
              >
                ✕
              </button>
            </div>

            <p style={styles.modalDescription}>{selected.description}</p>

            {selected.tactics.length > 0 && (
              <div style={styles.tagRow}>
                <span style={styles.tagLabel}>tactics:</span>
                {selected.tactics.map((t) => (
                  <span key={t} className="mono" style={styles.tag}>{t}</span>
                ))}
              </div>
            )}

            {selected.platforms.length > 0 && (
              <div style={styles.tagRow}>
                <span style={styles.tagLabel}>platforms:</span>
                {selected.platforms.map((p) => (
                  <span key={p} className="mono" style={styles.tag}>{p}</span>
                ))}
              </div>
            )}

            {selected.external_references?.length > 0 && (
              <div style={styles.refsBlock}>
                <span style={styles.tagLabel}>references:</span>
                {selected.external_references.map((ref, i) => (
                  ref.url && (
                    <a key={i} href={ref.url} target="_blank" rel="noreferrer" style={styles.refLink}>
                      &gt; {ref.source_name || ref.url}
                    </a>
                  )
                ))}
              </div>
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
  searchInput: {
    width: '100%',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '10px 14px',
    color: 'var(--text)',
    fontSize: '13px',
    marginBottom: '20px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '12px',
    minWidth: '500px',
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
    width: '520px',
    maxWidth: '100%',
    maxHeight: '85vh',
    overflowY: 'auto',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '24px',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '10px',
    marginBottom: '16px',
  },
  modalTitle: {
    fontSize: '16px',
    color: 'var(--accent)',
  },
  modalName: {
    fontSize: '13px',
    color: 'var(--text-muted)',
  },
  modalDescription: {
    fontSize: '13px',
    lineHeight: 1.6,
    marginBottom: '18px',
  },
  tagRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    alignItems: 'center',
    marginBottom: '12px',
  },
  tagLabel: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    marginRight: '4px',
  },
  tag: {
    fontSize: '11px',
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '3px 8px',
    color: 'var(--accent-dim)',
  },
  refsBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid var(--border)',
  },
  refLink: {
    fontSize: '12px',
    color: 'var(--accent)',
    textDecoration: 'none',
  },
}
