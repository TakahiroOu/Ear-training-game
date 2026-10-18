import assert from 'node:assert/strict'
import { test } from 'node:test'
import { DEFAULT_SETTINGS, answerComplete, checkTrainerAnswer } from './trainerRules.js'

const chord = { kind: 'chord', name: 'major', inversion: 1, root: 'C' }
const interval = { kind: 'interval', name: 'P5', inversion: null, root: null }
const askAll = { ...DEFAULT_SETTINGS, askInversion: true, askRoot: true }

test('only the name is needed by default', () => {
  assert.equal(checkTrainerAnswer({ name: 'major' }, chord, DEFAULT_SETTINGS).correct, true)
  assert.equal(checkTrainerAnswer({ name: 'minor' }, chord, DEFAULT_SETTINGS).correct, false)
  assert.equal(answerComplete({ name: 'major' }, chord, DEFAULT_SETTINGS), true)
})

test('inversion and root are checked when asked', () => {
  const result = checkTrainerAnswer({ name: 'major', inversion: 0, root: 'C' }, chord, askAll)
  assert.equal(result.correct, false)
  assert.deepEqual(result.parts, { name: true, inversion: false, root: true })
  assert.equal(checkTrainerAnswer({ name: 'major', inversion: 1, root: 'C' }, chord, askAll).correct, true)
  assert.equal(answerComplete({ name: 'major', inversion: 1 }, chord, askAll), false) // root missing
})

test('intervals never ask for inversion or root', () => {
  assert.equal(checkTrainerAnswer({ name: 'P5' }, interval, askAll).correct, true)
  assert.equal(answerComplete({ name: 'P5' }, interval, askAll), true)
})
