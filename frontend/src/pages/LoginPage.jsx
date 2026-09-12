import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/client.js'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/')
    } catch (err) {
      setError('ACCESS DENIED — identifiants incorrects')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.wrapper}>
      <div className="glow-border" style={styles.card}>
        <div style={styles.brand}>
          <span style={styles.brandMark}>&gt;_</span>
          <h1 style={styles.brandName}>CYBERTHREAT_RAG</h1>
        </div>
        <p style={styles.subtitle}>// analyst access — authentication required</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            login
            <input
              className="glow-border"
              style={styles.input}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              required
            />
          </label>
          <label style={styles.label}>
            password
            <input
              className="glow-border"
              style={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          {error && <p style={styles.error}>&gt; {error}</p>}

          <button className="glow-border" style={styles.button} type="submit" disabled={loading}>
            {loading ? '> connecting...' : '> connect'}
          </button>
        </form>
      </div>
    </div>
  )
}

const styles = {
  wrapper: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg)',
  },
  card: {
    width: '380px',
    padding: '40px 32px',
    background: 'var(--surface)',
    borderRadius: '2px',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '4px',
  },
  brandMark: {
    color: 'var(--accent)',
    fontSize: '18px',
  },
  brandName: {
    fontSize: '17px',
    letterSpacing: '0.04em',
  },
  subtitle: {
    color: 'var(--text-muted)',
    fontSize: '12px',
    margin: '6px 0 28px 0',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '18px',
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    fontSize: '12px',
    color: 'var(--accent-dim)',
    textTransform: 'lowercase',
  },
  input: {
    background: 'var(--bg)',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '10px 12px',
    color: 'var(--text)',
    fontSize: '14px',
  },
  error: {
    color: 'var(--critical)',
    fontSize: '12px',
    margin: 0,
  },
  button: {
    background: 'transparent',
    border: '1px solid var(--accent)',
    borderRadius: '2px',
    padding: '11px',
    color: 'var(--accent)',
    fontWeight: 600,
    fontSize: '14px',
    marginTop: '6px',
  },
}
