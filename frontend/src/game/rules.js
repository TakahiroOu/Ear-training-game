// Game rules as plain functions (no React), so they're easy to test: npm test

export const NOTE_NAMES = [
  'C3', 'C#3', 'D3', 'D#3', 'E3', 'F3', 'F#3', 'G3', 'G#3', 'A3', 'A#3', 'B3',
  'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4',
  'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5',
]
export const WHITE_NOTES = NOTE_NAMES.filter((note) => !note.includes('#'))
export const BLACK_NOTES = NOTE_NAMES.filter((note) => note.includes('#'))

export const MODES = [1, 2, 3, 4]
export const WIN_POINTS = 50
export const MAX_MISTAKES = 50

// Same scoring as the pygame version: harder modes give more points
// and cost fewer mistakes.
export const pointsFor = (mode) => mode
export const mistakesFor = (mode) => 5 - mode
// Right note letters but a wrong octave: half the points (rounded down), no mistakes
export const halfPointsFor = (mode) => Math.floor(mode / 2)

/** "C#4" -> "C#" (the note letter without its octave) */
export const pitchClass = (note) => note.slice(0, -1)

/** True when the player picked exactly the notes that were played (order doesn't matter). */
export function isCorrect(selected, answer) {
  return selected.length === answer.length && answer.every((note) => selected.includes(note))
}

/**
 * 'right'  - exactly the notes that were played
 * 'octave' - the right note letters, but at least one in the wrong octave
 * 'wrong'  - anything else
 * (same rules as classify() in backend/app/scoring.py)
 */
export function classifyAnswer(selected, answer) {
  if (isCorrect(selected, answer)) return 'right'
  const letters = (notes) => notes.map(pitchClass).sort().join(' ')
  return letters(selected) === letters(answer) ? 'octave' : 'wrong'
}

/**
 * How a piano key should look:
 *   'idle'     - normal white/black key
 *   'selected' - picked by the player (blue)
 *   after checking:
 *   'correct'  - picked and right (green)
 *   'octave'   - picked, right note letter but wrong octave (orange)
 *   'wrong'    - picked but not in the answer (red)
 *   'missed'   - in the answer but not picked (yellow)
 */
export function keyStatus(note, { selected, answer, result }) {
  const isSelected = selected.includes(note)
  if (!result) return isSelected ? 'selected' : 'idle'
  const isAnswer = answer.includes(note)
  if (isSelected && isAnswer) return 'correct'
  if (isSelected && answer.some((a) => pitchClass(a) === pitchClass(note))) return 'octave'
  if (isSelected) return 'wrong'
  if (isAnswer) return 'missed'
  return 'idle'
}
