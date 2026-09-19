import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { askQuery } from '../api/client.js'

export default function AssistantPage() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleAsk(e) {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError('')
    try {
      await askQuery(question)
      navigate('/reports')
    } catch (err) {
      setError('> ERROR — génération impossible, réessaie dans un instant')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <h2 style={styles.title}>&gt; ai threat intelligence assistant</h2>
      <p style={styles.subtitle}>
        // pose une question en langage naturel sur les CVE, KEV ou techniques ATT&CK indexées
      </p>

      <form onSubmit={handleAsk} style={styles.queryForm}>
        <input
          className="glow-border"
          style={styles.queryInput}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="ex : quelles sont les CVE critiques exploitées actuellement ?"
          disabled={loading}
          autoFocus
        />
        <button className="glow-border" style={styles.queryButton} type="submit" disabled={loading}>
          analyser
        </button>
      </form>

      {loading && <LoadingSpinner label="génération du rapport CTI" />}
      {error && <p style={styles.error}>{error}</p>}
      {!loading && (
        <p style={styles.hint}>&gt; le rapport généré s'affichera dans l'onglet "reports"</p>
      )}

      <div style={styles.examples}>
        <span style={styles.examplesLabel}>exemples :</span>
        {[
          "Quelles vulnérabilités critiques sont activement exploitées ?",
          "Quelles techniques ATT&CK ciblent les applications exposées sur Internet ?",
          "Résume les risques liés aux escalades de privilèges récentes.",
        ].map((ex) => (
          <button
            key={ex}
            className="glow-border"
            style={styles.exampleChip}
            onClick={() => setQuestion(ex)}
            type="button"
          >
            {ex}
          </button>
        ))}
      </div>
    </Layout>
  )
}

const styles = {
  title: {
    fontSize: '15px',
    color: 'var(--accent)',
    marginBottom: '6px',
  },
  subtitle: {
    fontSize: '12px',
    color: 'var(--text-muted)',
    marginBottom: '24px',
  },
  queryForm: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
  },
  queryInput: {
    flex: '1 1 260px',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '12px 14px',
    color: 'var(--text)',
    fontSize: '14px',
  },
  queryButton: {
    background: 'transparent',
    border: '1px solid var(--accent)',
    borderRadius: '2px',
    padding: '11px 22px',
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
  hint: {
    color: 'var(--text-muted)',
    fontSize: '12px',
    marginTop: '14px',
  },
  examples: {
    marginTop: '32px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    alignItems: 'flex-start',
  },
  examplesLabel: {
    fontSize: '11px',
    color: 'var(--text-muted)',
    marginBottom: '4px',
  },
  exampleChip: {
    background: 'transparent',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '8px 12px',
    color: 'var(--text-muted)',
    fontSize: '12px',
    textAlign: 'left',
  },
}
