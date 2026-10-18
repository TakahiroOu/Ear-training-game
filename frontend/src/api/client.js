// Every call to the Python backend goes through this file.
// In development, Vite forwards /api to the backend (see vite.config.js).
// For the phone app or a separate server later, set VITE_API_URL.
const API_URL = import.meta.env.VITE_API_URL || ''

async function request(path, { token, method = 'GET', body } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}` // the login token from Supabase
  if (body) headers['Content-Type'] = 'application/json'

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) throw new Error(`Server error ${response.status}`)
  return response.json()
}

/** Ask the server for a new question: a list of note names like ["C4", "E4", "G4"]. */
export async function fetchQuestion(mode) {
  const data = await request(`/api/questions?mode=${mode}`)
  return data.notes
}

/** Logged-in players: start saving a new game. Returns the game's id. */
export async function startSession(token) {
  const data = await request('/api/sessions', { token, method: 'POST' })
  return data.id
}

/** Logged-in players: save one checked question. The server calculates the score itself. */
export function saveAnswer(token, sessionId, answer) {
  return request(`/api/sessions/${sessionId}/answers`, { token, method: 'POST', body: answer })
}

export function fetchStats(token) {
  return request('/api/me/stats', { token })
}
