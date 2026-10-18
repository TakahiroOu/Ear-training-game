// Keys (調性) and how to spell notes in them.
// Inside the app, notes are always named with sharps ("A#4"), like the sound files.
// For the player, spellNote() writes them the way they appear in the key ("B♭4" in F major).
import { NOTE_NAMES } from './rules.js'

// `id` is what the server understands (tonic written with a sharp), `tonic` is how musicians write it.
export const KEYS = [
  { id: 'C-major', tonic: 'C', en: 'C major', ja: 'ハ長調' },
  { id: 'G-major', tonic: 'G', en: 'G major', ja: 'ト長調' },
  { id: 'D-major', tonic: 'D', en: 'D major', ja: 'ニ長調' },
  { id: 'A-major', tonic: 'A', en: 'A major', ja: 'イ長調' },
  { id: 'E-major', tonic: 'E', en: 'E major', ja: 'ホ長調' },
  { id: 'B-major', tonic: 'B', en: 'B major', ja: 'ロ長調' },
  { id: 'F#-major', tonic: 'F♯', en: 'F♯ major', ja: '嬰ヘ長調' },
  { id: 'C#-major', tonic: 'D♭', en: 'D♭ major', ja: '変ニ長調' },
  { id: 'G#-major', tonic: 'A♭', en: 'A♭ major', ja: '変イ長調' },
  { id: 'D#-major', tonic: 'E♭', en: 'E♭ major', ja: '変ホ長調' },
  { id: 'A#-major', tonic: 'B♭', en: 'B♭ major', ja: '変ロ長調' },
  { id: 'F-major', tonic: 'F', en: 'F major', ja: 'ヘ長調' },
  { id: 'A-minor', tonic: 'A', en: 'A minor', ja: 'イ短調' },
  { id: 'E-minor', tonic: 'E', en: 'E minor', ja: 'ホ短調' },
  { id: 'B-minor', tonic: 'B', en: 'B minor', ja: 'ロ短調' },
  { id: 'F#-minor', tonic: 'F♯', en: 'F♯ minor', ja: '嬰ヘ短調' },
  { id: 'C#-minor', tonic: 'C♯', en: 'C♯ minor', ja: '嬰ハ短調' },
  { id: 'G#-minor', tonic: 'G♯', en: 'G♯ minor', ja: '嬰ト短調' },
  { id: 'D#-minor', tonic: 'E♭', en: 'E♭ minor', ja: '変ホ短調' },
  { id: 'A#-minor', tonic: 'B♭', en: 'B♭ minor', ja: '変ロ短調' },
  { id: 'F-minor', tonic: 'F', en: 'F minor', ja: 'ヘ短調' },
  { id: 'C-minor', tonic: 'C', en: 'C minor', ja: 'ハ短調' },
  { id: 'G-minor', tonic: 'G', en: 'G minor', ja: 'ト短調' },
  { id: 'D-minor', tonic: 'D', en: 'D minor', ja: 'ニ短調' },
]

const LETTERS = 'CDEFGAB'
const LETTER_PITCH = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }
const MAJOR = [0, 2, 4, 5, 7, 9, 11]
const HARMONIC_MINOR = [0, 2, 3, 5, 7, 8, 11]
const ACCIDENTALS = { '-2': '𝄫', '-1': '♭', 0: '', 1: '♯', 2: '𝄪' }
const SHARP_NAMES = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']
const FLAT_NAMES = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B']

export const findKey = (id) => KEYS.find((key) => key.id === id) ?? null

const pitchOf = (note) => NOTE_NAMES.indexOf(note) % 12
const octaveOf = (note) => Number(note.slice(-1))

/** { pitch class -> { letter, accidental } } for the notes of a key, spelled with the key's own letters. */
function keySpellings(key) {
  const tonicLetter = key.tonic[0]
  const tonicPitch = (LETTER_PITCH[tonicLetter] + (key.tonic.includes('♯') ? 1 : key.tonic.includes('♭') ? -1 : 0) + 12) % 12
  const isMinor = key.id.endsWith('minor')
  const steps = isMinor ? HARMONIC_MINOR : MAJOR
  const spellings = {}
  const add = (degree, step) => {
    const letter = LETTERS[(LETTERS.indexOf(tonicLetter) + degree) % 7]
    const pitch = (tonicPitch + step) % 12
    let alter = (pitch - LETTER_PITCH[letter] + 12) % 12
    if (alter > 6) alter -= 12
    spellings[pitch] = { letter, accidental: ACCIDENTALS[alter], alter }
  }
  steps.forEach((step, degree) => add(degree, step))
  if (isMinor) add(6, 10) // natural 7th as well (used in chords other than V and VII)
  return spellings
}

/** "A#4" -> "B♭4" in F major. Without a key, sharps are used. */
export function spellNote(note, keyId) {
  const key = findKey(keyId)
  const pitch = pitchOf(note)
  let octave = octaveOf(note)
  const spelled = key && keySpellings(key)[pitch]
  if (!spelled) {
    const flatKey = key && (key.tonic.includes('♭') || ['F-major', 'D-minor', 'G-minor', 'C-minor', 'F-minor'].includes(key.id))
    return (flatKey ? FLAT_NAMES : SHARP_NAMES)[pitch] + octave
  }
  // B♯ sounds like the next octave's C, and C♭ like the previous octave's B
  if (spelled.letter === 'B' && spelled.alter > 0 && pitch < 2) octave -= 1
  if (spelled.letter === 'C' && spelled.alter < 0 && pitch > 9) octave += 1
  return spelled.letter + spelled.accidental + octave
}

/** The key's tonic chord around middle C, to hear the key before the questions. */
export function tonicChord(keyId) {
  const key = findKey(keyId)
  const root = 12 + ((LETTER_PITCH[key.tonic[0]] + (key.tonic.includes('♯') ? 1 : key.tonic.includes('♭') ? -1 : 0) + 12) % 12)
  const third = key.id.endsWith('minor') ? 3 : 4
  return [root, root + third, root + 7].map((index) => NOTE_NAMES[index])
}
