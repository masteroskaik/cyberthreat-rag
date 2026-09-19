import { useState, useEffect } from 'react'

const FRAMES = ['[    ]', '[=   ]', '[==  ]', '[=== ]', '[ ===]', '[  ==]', '[   =]']

export default function LoadingSpinner({ label = 'processing' }) {
  const [frame, setFrame] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setFrame((f) => (f + 1) % FRAMES.length)
    }, 120)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={styles.wrapper}>
      <span className="mono" style={styles.bar}>{FRAMES[frame]}</span>
      <span style={styles.label}>&gt; {label}...</span>
    </div>
  )
}

const styles = {
  wrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '14px 0',
    color: 'var(--accent)',
    fontSize: '13px',
  },
  bar: {
    color: 'var(--accent)',
  },
  label: {
    color: 'var(--text-muted)',
  },
}
