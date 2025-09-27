const BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || ''

type HttpOptions = {
  method?: string
  body?: any
  headers?: Record<string, string>
}

async function http(path: string, opts: HttpOptions = {}) {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url, {
    method: opts.method || 'GET',
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    body: opts.body ? JSON.stringify(opts.body) : undefined
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json()
}

export const api = {
  health: () => http('/health'),
  inventory: () => http('/api/inventory'),
  tenders: () => http('/api/tenders'),
  salesDaily: () => http('/api/sales/daily')
}
