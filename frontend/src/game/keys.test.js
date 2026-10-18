import assert from 'node:assert/strict'
import { test } from 'node:test'
import { KEYS, spellNote, tonicChord } from './keys.js'

test('24 keys', () => {
  assert.equal(KEYS.length, 24)
})

test('notes are spelled the way the key writes them', () => {
  assert.equal(spellNote('A#4', 'F-major'), 'B♭4')
  assert.equal(spellNote('A#4', 'B-major'), 'A♯4')
  assert.equal(spellNote('C#4', 'D-minor'), 'C♯4') // leading tone in D minor is C♯, not D♭
  assert.equal(spellNote('C4', 'D-minor'), 'C4') // natural 7th
  assert.equal(spellNote('F4', 'F#-major'), 'E♯4')
  assert.equal(spellNote('G4', 'G#-minor'), 'F𝄪4') // leading tone of G♯ minor
  assert.equal(spellNote('C4', 'C#-minor'), 'B♯3') // B♯3 sounds the same as C4
  assert.equal(spellNote('D#4', 'A#-minor'), 'E♭4')
})

test('without a key, or for notes outside it, sharps or flats are used', () => {
  assert.equal(spellNote('A#4', null), 'A♯4')
  assert.equal(spellNote('F#4', 'F-major'), 'G♭4') // chromatic note in a flat key
  assert.equal(spellNote('D#4', 'G-major'), 'D♯4')
})

test('tonic chords', () => {
  assert.deepEqual(tonicChord('C-major'), ['C4', 'E4', 'G4'])
  assert.deepEqual(tonicChord('A-minor'), ['A4', 'C5', 'E5'])
  assert.deepEqual(tonicChord('A#-major'), ['A#4', 'D5', 'F5'])
})
