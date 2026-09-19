const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function getToken() {
  return localStorage.getItem('cti_token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    localStorage.removeItem('cti_token')
    window.location.href = '/login'
    throw new Error('Session expirée')
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Erreur ${response.status}`)
  }

  return response.json()
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  localStorage.setItem('cti_token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('cti_token')
}

export function isAuthenticated() {
  return Boolean(getToken())
}

export async function askQuery(question, targetType = null, targetId = null) {
  return request('/query', {
    method: 'POST',
    body: JSON.stringify({ question, target_type: targetType, target_id: targetId }),
  })
}

export async function listReports(limit = 50) {
  return request(`/reports?limit=${limit}`)
}

export async function getReport(reportId) {
  return request(`/reports/${reportId}`)
}

export async function downloadReportDocx(reportId) {
  const token = getToken()
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/export/docx`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw new Error('Export impossible')

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `rapport_cti_${reportId}.docx`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export async function listCves(limit = 20, offset = 0, severity = null) {
  const params = new URLSearchParams({ limit, offset })
  if (severity) params.append('severity', severity)
  return request(`/cves?${params.toString()}`)
}

export async function getCve(cveId) {
  return request(`/cves/${cveId}`)
}

export async function listTechniques(search = '', limit = 100, offset = 0) {
  const params = new URLSearchParams({ limit, offset })
  if (search) params.append('search', search)
  return request(`/techniques?${params.toString()}`)
}

export async function getTechnique(techniqueId) {
  return request(`/techniques/${techniqueId}`)
}

export async function checkHealth() {
  return request('/health')
}

export async function getStats() {
  return request('/stats')
}

export async function getDataSources() {
  return request('/data-sources')
}
