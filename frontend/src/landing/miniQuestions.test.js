import assert from 'node:assert/strict'
import { test } from 'node:test'
import { NOTE_NAMES } from '../game/rules.js'
import { MINI_CHORDS, MINI_DEGREES, MINI_INTERVALS, QUESTION_MAKERS } from './miniQuestions.js'

const index = (n) => NOTE_NAMES.indexOf(n)
const steps = (notes) => notes.map((n) => index(n) - index(notes[0]))

test('every question uses existing piano samples and matches its answer', () => {
  for (let i = 0; i < 500; i++) {
    const interval = QUESTION_MAKERS.interval()
    assert.ok(interval.notes.every((n) => index(n) >= 0))
    assert.deepEqual(steps(interval.notes), [0, MINI_INTERVALS[interval.answer]])

    const chord = QUESTION_MAKERS.chord()
    assert.ok(chord.notes.every((n) => index(n) >= 0))
    assert.deepEqual(steps(chord.notes), MINI_CHORDS[chord.answer])

    const degree = QUESTION_MAKERS.degree()
    assert.equal(index(degree.notes[0]) - index('C4'), MINI_DEGREES[degree.answer])
  }
})
