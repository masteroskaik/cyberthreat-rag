import { useState, useEffect } from 'react'
import Layout from '../components/Layout.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { getStats, getDataSources } from '../api/client.js'

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getStats(), getDataSources()])
      .then(([s, ds]) => {
        setStats(s)
        setSources(ds)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <Layout>
        <LoadingSpinner label="chargement du dashboard" />
      </Layout>
    )
  }

  if (!stats) {
    return (
      <Layout>
        <p style={{ color: 'var(--critical)', fontSize: '13px' }}>&gt; impossible de charger les statistiques</p>
      </Layout>
    )
  }

  const sev = stats.severity_breakdown
  const maxSev = Math.max(sev.critical, sev.high, sev.medium, sev.low, 1)
  const maxTactic = Math.max(...stats.top_tactics.map((t) => t.count), 1)

  return (
    <Layout>
      <h2 style={styles.title}>&gt; threat intelligence dashboard</h2>

      <section style={styles.kpiRow}>
        <KpiCard label="total_cve" value={stats.total_cves} />
        <KpiCard label="critical" value={sev.critical} accent="critical" />
        <KpiCard label="high" value={sev.high} accent="accent" />
        <KpiCard label="cisa_kev" value={stats.total_kev} accent="critical" />
      </section>

      <div style={styles.grid}>
        <Panel title="threat priority">
          <PriorityBar label="critical + kev" value={stats.critical_and_kev} max={maxSev} critical />
          <PriorityBar label="high + kev" value={stats.high_and_kev} max={maxSev} />
          <PriorityBar label="critical" value={sev.critical} max={maxSev} critical />
          <PriorityBar label="high" value={sev.high} max={maxSev} />
          <PriorityBar label="medium" value={sev.medium} max={maxSev} />
          <PriorityBar label="low" value={sev.low} max={maxSev} />
        </Panel>

        <Panel title="cisa kev — top priority">
          {stats.top_kev.length === 0 ? (
            <p style={styles.empty}>&gt; aucune donnée KEV</p>
          ) : (
            <div style={styles.kevList}>
              {stats.top_kev.map((k) => (
                <div key={k.id} className="mono" style={styles.kevRow}>
                  <span style={styles.kevId}>{k.id}</span>
                  <span style={{
                    ...styles.kevSev,
                    color: k.cvss_severity === 'CRITICAL' ? 'var(--critical)' : 'var(--accent)',
                  }}>
                    {k.cvss_severity || '—'}
                  </span>
                  <span>{k.cvss_score ?? '—'}</span>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="mitre att&ck — top tactics">
          {stats.top_tactics.length === 0 ? (
            <p style={styles.empty}>&gt; aucune donnée ATT&CK</p>
          ) : (
            stats.top_tactics.map((t) => (
              <PriorityBar key={t.tactic} label={t.tactic} value={t.count} max={maxTactic} />
            ))
          )}
        </Panel>

        <Panel title="data sources">
          <div style={styles.sourcesList}>
            {['nvd', 'cisa_kev', 'mitre_attack'].map((key) => {
              const entry = sources.find((s) => s.source === key)
              return (
                <div key={key} style={styles.sourceRow}>
                  <span className={entry ? 'pulse-dot' : ''} style={{ color: entry ? 'var(--accent)' : 'var(--text-muted)' }}>
                    {entry ? '' : '○'}
                  </span>
                  <span className="mono" style={styles.sourceName}>{key}</span>
                  <span style={styles.sourceMeta}>
                    {entry
                      ? `${entry.records_count ?? '?'} enregistrements — ${new Date(entry.last_run_at).toLocaleString()}`
                      : 'jamais ingérée'}
                  </span>
                </div>
              )
            })}
          </div>
        </Panel>
      </div>
    </Layout>
  )
}

function KpiCard({ label, value, accent }) {
  return (
    <div className="glow-border" style={styles.kpiCard}>
      <span className="mono" style={{
        ...styles.kpiValue,
        color: accent === 'critical' ? 'var(--critical)' : 'var(--accent)',
      }}>
        {value}
      </span>
      <span style={styles.kpiLabel}>{label}</span>
    </div>
  )
}

function Panel({ title, children }) {
  return (
    <div className="glow-border" style={styles.panel}>
      <h3 style={styles.panelTitle}>&gt; {title}</h3>
      <div style={styles.panelBody}>{children}</div>
    </div>
  )
}

function PriorityBar({ label, value, max, critical }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div style={styles.barRow}>
      <span style={styles.barLabel}>{label}</span>
      <div style={styles.barTrack}>
        <div style={{
          ...styles.barFill,
          width: `${pct}%`,
          background: critical ? 'var(--critical)' : 'var(--accent)',
        }} />
      </div>
      <span className="mono" style={styles.barValue}>{value}</span>
    </div>
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
    fontSize: '12px',
  },
  kpiRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '14px',
    marginBottom: '24px',
  },
  kpiCard: {
    flex: '1 1 140px',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '16px 18px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  kpiValue: {
    fontSize: '26px',
    fontWeight: 700,
  },
  kpiLabel: {
    fontSize: '11px',
    color: 'var(--text-muted)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '16px',
  },
  panel: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '18px',
  },
  panelTitle: {
    fontSize: '13px',
    color: 'var(--accent)',
    marginBottom: '16px',
  },
  panelBody: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  barRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '12px',
  },
  barLabel: {
    width: '110px',
    flexShrink: 0,
    color: 'var(--text-muted)',
    textTransform: 'lowercase',
  },
  barTrack: {
    flex: 1,
    height: '8px',
    background: 'var(--bg)',
    borderRadius: '1px',
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
  },
  barValue: {
    width: '40px',
    textAlign: 'right',
    color: 'var(--text)',
  },
  kevList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  kevRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    padding: '6px 0',
    borderBottom: '1px solid var(--border)',
  },
  kevId: {
    color: 'var(--text)',
  },
  kevSev: {
    fontWeight: 600,
  },
  sourcesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  sourceRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '12px',
    flexWrap: 'wrap',
  },
  sourceName: {
    width: '90px',
    color: 'var(--text)',
  },
  sourceMeta: {
    color: 'var(--text-muted)',
    fontSize: '11px',
  },
}
