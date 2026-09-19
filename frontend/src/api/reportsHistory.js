const STORAGE_KEY = 'cti_reports_history'
const MAX_HISTORY = 50

export function getReportsHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

export function saveReportToHistory(question, report) {
  const history = getReportsHistory()
  const entry = {
    id: Date.now(),
    question,
    answer: report.answer,
    sources: report.sources || [],
    createdAt: new Date().toISOString(),
  }
  const updated = [entry, ...history].slice(0, MAX_HISTORY)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  return entry
}

export function clearReportsHistory() {
  localStorage.removeItem(STORAGE_KEY)
}
