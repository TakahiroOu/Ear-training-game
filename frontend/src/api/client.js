// Every call to the Python backend goes through this file.
// In development, Vite forwards /api to the backend (see vite.config.js).
// For the phone app or a separate server later, set VITE_API_URL.
const API_URL = import.meta.env.VITE_API_URL || ''

async function request(path, { token, method = 'GET', body, binary = false } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}` // the login token from Supabase
  if (body) headers['Content-Type'] = 'application/json'

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const error = new Error(`Server error ${response.status}`)
    error.status = response.status // e.g. 422 = the server didn't accept what we sent
    error.detail = await response.json().then((data) => data.detail).catch(() => null)
    throw error
  }
  return binary ? response.arrayBuffer() : response.json()
}

/**
 * Ask the server for a new question: a list of note names like ["C4", "E4", "G4"].
 * With a key (e.g. "D-major"), only notes and chords of that key are used.
 */
export async function fetchQuestion(mode, key = null) {
  const params = new URLSearchParams({ mode })
  if (key) params.set('key', key)
  const data = await request(`/api/questions?${params}`)
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

/** Interval & chord trainer: a question that fits the settings. Returns { notes, answer }. */
export function fetchTrainerQuestion(settings) {
  const { intervals, triads, sevenths, inversions, low, high } = settings
  return request('/api/trainer/question', {
    method: 'POST',
    body: { intervals, triads, sevenths, inversions, low, high },
  })
}

/** Logged-in players: save a finished trainer test. */
export function saveTrainerResult(token, result) {
  return request('/api/trainer/results', { token, method: 'POST', body: result })
}

// ---------- profile ----------

export function fetchMe(token) {
  return request('/api/me', { token })
}

/** Choose the name shown on leaderboards. */
export function setUsername(token, username) {
  return request('/api/me', { token, method: 'PATCH', body: { username } })
}

// ---------- competitions ----------

/** { ranked: [easy, mixed], classes: [...] } */
export function fetchCompetitions(token) {
  return request('/api/competitions', { token })
}

export function createClassCompetition(token, competition) {
  return request('/api/competitions', { token, method: 'POST', body: competition })
}

export function findCompetitionByCode(token, code) {
  return request(`/api/competitions/code/${encodeURIComponent(code)}`, { token })
}

/** period: 'all' or 'week' (ranked competitions show every finished run) */
export function fetchLeaderboard(token, competitionId, period = 'all') {
  return request(`/api/competitions/${competitionId}/leaderboard?period=${period}`, { token })
}

// ---------- live rooms ----------

/** Create a live room. Returns { code }. */
export function createRoom(token) {
  return request('/api/rooms', { token, method: 'POST' })
}

/** WebSocket address of a room, e.g. ws://localhost:5173/api/rooms/ABC123/ws */
export function roomSocketUrl(code) {
  const base = new URL(API_URL || window.location.origin)
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${base.origin}/api/rooms/${encodeURIComponent(code)}/ws`
}

/** Ranked: start a 20-question run (or continue an unfinished one). Class: your one attempt. */
export function enterCompetition(token, competitionId, playerName) {
  const body = playerName ? { player_name: playerName } : undefined // continuing a run needs no name
  return request(`/api/competitions/${competitionId}/entries`, { token, method: 'POST', body })
}

/** Creator only: close a class competition (its leaderboard stays visible). */
export function closeCompetition(token, competitionId) {
  return request(`/api/competitions/${competitionId}/close`, { token, method: 'POST' })
}

/** The current question as audio (the server never sends its note names before you answer). */
export function fetchQuestionAudio(token, entryId) {
  return request(`/api/entries/${entryId}/audio`, { token, binary: true })
}

export function answerCompetition(token, entryId, index, givenNotes) {
  return request(`/api/entries/${entryId}/answers`, {
    token,
    method: 'POST',
    body: { index, given_notes: givenNotes },
  })
}

export function fetchStats(token) {
  return request('/api/me/stats', { token })
}
