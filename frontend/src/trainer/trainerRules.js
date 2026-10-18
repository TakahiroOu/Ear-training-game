// Interval & chord trainer: the choices and how answers are checked (no React, so easy to test).
// The names match backend/app/trainer.py.

export const INTERVALS = ['m2', 'M2', 'm3', 'M3', 'P4', 'TT', 'P5', 'm6', 'M6', 'm7', 'M7', 'P8']
export const TRIADS = ['major', 'minor', 'diminished', 'augmented']
export const SEVENTHS = ['dominant7', 'minor7', 'major7', 'half_diminished7', 'diminished7']
export const INVERSIONS = [0, 1, 2, 3]
export const ROOTS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
export const NOTE_LENGTHS = [0.5, 1, 2, 4]
export const TEST_LENGTH = 20

export const DEFAULT_SETTINGS = {
  intervals: ['m3', 'M3', 'P4', 'P5', 'P8'],
  triads: ['major', 'minor'],
  sevenths: [],
  inversions: [0],
  low: 'C3',
  high: 'B4',
  playback: 'harmonic', // or 'melodic'
  askInversion: false,
  askRoot: false,
  noteLength: 1,
  mode: 'practice', // or 'test'
}

/** Which parts of the answer the player has to give for this question. */
export function questionsAsked(answer, settings) {
  const isChord = answer.kind === 'chord'
  return {
    name: true,
    inversion: isChord && settings.askInversion,
    root: isChord && settings.askRoot,
  }
}

/** Is everything the player was asked for right? Also says which parts were right. */
export function checkTrainerAnswer(given, answer, settings) {
  const asked = questionsAsked(answer, settings)
  const parts = {
    name: given.name === answer.name,
    inversion: !asked.inversion || given.inversion === answer.inversion,
    root: !asked.root || given.root === answer.root,
  }
  return { correct: parts.name && parts.inversion && parts.root, parts }
}

/** The player has chosen everything they were asked for. */
export function answerComplete(given, answer, settings) {
  const asked = questionsAsked(answer, settings)
  return (
    given.name != null &&
    (!asked.inversion || given.inversion != null) &&
    (!asked.root || given.root != null)
  )
}
