// All sound playing lives here (replaces pygame.mixer / AudioCreator).
import * as Tone from 'tone'
import { NOTE_NAMES } from '../game/rules.js'

// "C4" -> "C4.mp3", "C#4" -> "C4s.mp3" (the sample files put "s" for sharp at the end)
const fileFor = (note) => (note.includes('#') ? note.replace('#', '') + 's' : note) + '.mp3'

let piano = null
let rightSound = null
let wrongSound = null

/**
 * Load the piano samples. Must be called from a click or tap:
 * browsers (especially phones) block sound until the user interacts with the page.
 */
export async function loadSounds() {
  await Tone.start()
  if (!piano) {
    piano = new Tone.Sampler({
      urls: Object.fromEntries(NOTE_NAMES.map((note) => [note, fileFor(note)])),
      baseUrl: '/sounds/',
      release: 1,
    }).toDestination()
    rightSound = new Tone.Player('/sounds/right_answer.mp3').toDestination()
    wrongSound = new Tone.Player('/sounds/false_answer.mp3').toDestination()
  }
  await Tone.loaded()
}

/** Play one or more notes at exactly the same moment, e.g. playNotes(['C4', 'E4', 'G4']). */
export function playNotes(notes, seconds = 3) {
  piano.triggerAttackRelease(notes, seconds)
}

/** Play notes one after another, each lasting `seconds`. */
export function playMelody(notes, seconds = 1) {
  const now = Tone.now()
  notes.forEach((note, i) => piano.triggerAttackRelease(note, seconds, now + i * seconds))
}

export function playResult(correct) {
  ;(correct ? rightSound : wrongSound).start()
}
