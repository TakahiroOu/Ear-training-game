// Every call to the Python backend goes through this file.
// In development, Vite forwards /api to the backend (see vite.config.js).
// For the phone app or a separate server later, set VITE_API_URL.
const API_URL = import.meta.env.VITE_API_URL || ''

/** Ask the server for a new question: a list of note names like ["C4", "E4", "G4"]. */
export async function fetchQuestion(mode) {
  const response = await fetch(`${API_URL}/api/questions?mode=${mode}`)
  if (!response.ok) throw new Error(`Server error ${response.status}`)
  const data = await response.json()
  return data.notes
}
