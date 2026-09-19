import { NavLink, useNavigate } from 'react-router-dom'
import { logout } from '../api/client.js'

const NAV_ITEMS = [
  { to: '/', label: 'dashboard', end: true },
  { to: '/assistant', label: 'assistant' },
  { to: '/reports', label: 'reports' },
  { to: '/techniques', label: 'techniques' },
  { to: '/cves', label: 'cves' },
]

export default function Layout({ children }) {
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-layout">
      <div className="scanline" />
      <aside className="app-sidebar">
        <div style={styles.brand}>
          <span style={{ color: 'var(--accent)' }}>&gt;_</span>
          <span style={styles.brandName}>CYBERTHREAT_RAG</span>
        </div>
        <nav className="app-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => 'app-nav-item' + (isActive ? ' app-nav-item-active' : '')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button className="glow-border" style={styles.logoutButton} onClick={handleLogout}>
          &gt; logout
        </button>
      </aside>

      <main className="app-main">{children}</main>
    </div>
  )
}

const styles = {
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '32px',
  },
  brandName: {
    fontSize: '12px',
    fontWeight: 600,
    letterSpacing: '0.03em',
  },
  logoutButton: {
    background: 'transparent',
    border: '1px solid var(--border)',
    borderRadius: '2px',
    padding: '9px',
    color: 'var(--text-muted)',
    fontSize: '12px',
  },
}
