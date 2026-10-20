// Questions for the small trainers on the guide pages. They're made in the browser
// (no server needed), so the guide pages work instantly even while the free server sleeps.
import { NOTE_NAMES } from '../game/rules.js'

const pick = (items, random) => items[Math.floor(random() * items.length)]
const note = (index) => NOTE_NAMES[index]
const C4 = NOTE_NAMES.indexOf('C4')

// ---------- interval: two notes, name the distance ----------
export const MINI_INTERVALS = { m2: 1, M2: 2, m3: 3, M3: 4, P4: 5, P5: 7, M6: 9, P8: 12 }

export function intervalQuestion(random = Math.random) {
  const answer = pick(Object.keys(MINI_INTERVALS), random)
  const low = C4 + Math.floor(random() * 12) // C4 ... B4, so the top note stays within the samples
  return { kind: 'interval', answer, notes: [note(low), note(low + MINI_INTERVALS[answer])] }
}

// ---------- chord: three notes together, name the triad ----------
export const MINI_CHORDS = { major: [0, 4, 7], minor: [0, 3, 7], diminished: [0, 3, 6], augmented: [0, 4, 8] }

export function chordQuestion(random = Math.random) {
  const answer = pick(Object.keys(MINI_CHORDS), random)
  const root = C4 - 12 + Math.floor(random() * 12) // C3 ... B3
  return { kind: 'chord', answer, notes: MINI_CHORDS[answer].map((step) => note(root + step)) }
}

// ---------- degree: hear C (ド) first, then name the next note of C major ----------
export const MINI_DEGREES = { do: 0, re: 2, mi: 4, fa: 5, so: 7, la: 9, ti: 11 }

export function degreeQuestion(random = Math.random) {
  const answer = pick(Object.keys(MINI_DEGREES), random)
  return { kind: 'degree', answer, reference: 'C4', notes: [note(C4 + MINI_DEGREES[answer])] }
}

export const QUESTION_MAKERS = { interval: intervalQuestion, chord: chordQuestion, degree: degreeQuestion }
export const CHOICES = {
  interval: Object.keys(MINI_INTERVALS),
  chord: Object.keys(MINI_CHORDS),
  degree: Object.keys(MINI_DEGREES),
}
