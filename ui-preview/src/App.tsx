import React, { useEffect, useState } from 'react'
import { api } from './lib/api'

type Screen = 'dashboard' | 'inventory' | 'tenders'

export default function App() {
  const [screen, setScreen] = useState<Screen>('dashboard')
  const [health, setHealth] = useState('checking...')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.health()
      .then(() => setHealth('ok'))
      .catch(e => setHealth(`not reachable (${e.message})`))
  }, [])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 16, maxWidth: 900, margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>BERHAN ERP — UI Preview</h1>
        <small>API health: <strong>{health}</strong></small>
      </header>

      <nav style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <button onClick={() => setScreen('dashboard')}>Dashboard</button>
        <button onClick={() => setScreen('inventory')}>Inventory</button>
        <button onClick={() => setScreen('tenders')}>Tenders</button>
      </nav>

      <main style={{ marginTop: 16 }}>
        {screen === 'dashboard' && <Dashboard setError={setError} />}
        {screen === 'inventory' && <Inventory setError={setError} />}
        {screen === 'tenders' && <Tenders setError={setError} />}
      </main>

      {error && (
        <pre style={{ background: '#fee', padding: 12, marginTop: 16, border: '1px solid #f99' }}>
          {error}
        </pre>
      )}
    </div>
  )
}

function Dashboard({ setError }: { setError: (s: string|null) => void }) {
  const [sales, setSales] = useState<any[]>([])
  useEffect(() => {
    api.salesDaily().then(setSales).catch(e => setError(e.message))
  }, [])
  return (
    <section>
      <h2>Daily Sales</h2>
      <ul>
        {sales.map((row, i) => (
          <li key={i}>{row.date}: {row.total}</li>
        ))}
      </ul>
    </section>
  )
}

function Inventory({ setError }: { setError: (s: string|null) => void }) {
  const [items, setItems] = useState<any[]>([])
  useEffect(() => {
    api.inventory().then(setItems).catch(e => setError(e.message))
  }, [])
  return (
    <section>
      <h2>Inventory</h2>
      <table>
        <thead><tr><th>SKU</th><th>Name</th><th>Qty</th></tr></thead>
        <tbody>
          {items.map((i, idx) => (
            <tr key={idx}><td>{i.sku}</td><td>{i.name}</td><td>{i.qty}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function Tenders({ setError }: { setError: (s: string|null) => void }) {
  const [rows, setRows] = useState<any[]>([])
  useEffect(() => {
    api.tenders().then(setRows).catch(e => setError(e.message))
  }, [])
  return (
    <section>
      <h2>Tenders</h2>
      <ol>
        {rows.map((t, i) => <li key={i}>{t.title} — status: {t.status}</li>)}
      </ol>
    </section>
  )
}
