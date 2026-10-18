// Run with: npm test   (uses Node's built-in test runner, no extra library needed)
import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  BLACK_NOTES,
  WHITE_NOTES,
  isCorrect,
  keyStatus,
  mistakesFor,
  pointsFor,
} from './rules.js'

test('piano has 21 white and 15 black keys', () => {
  assert.equal(WHITE_NOTES.length, 21)
  assert.equal(BLACK_NOTES.length, 15)
})

test('answer is correct only with exactly the same notes, in any order', () => {
  assert.ok(isCorrect(['E4', 'C4', 'G4'], ['C4', 'E4', 'G4']))
  assert.ok(!isCorrect(['C4', 'E4'], ['C4', 'E4', 'G4'])) // one missing
  assert.ok(!isCorrect(['C4', 'E4', 'G4', 'B4'], ['C4', 'E4', 'G4'])) // one extra
  assert.ok(!isCorrect(['C5'], ['C4'])) // right note, wrong octave
})

test('scoring matches the original game', () => {
  assert.deepEqual([1, 2, 3, 4].map(pointsFor), [1, 2, 3, 4])
  assert.deepEqual([1, 2, 3, 4].map(mistakesFor), [4, 3, 2, 1])
})

test('key colors before and after checking', () => {
  const round = { selected: ['C4', 'D4'], answer: ['C4', 'E4'] }
  assert.equal(keyStatus('C4', { ...round, result: null }), 'selected')
  assert.equal(keyStatus('E4', { ...round, result: null }), 'idle')
  assert.equal(keyStatus('C4', { ...round, result: 'wrong' }), 'correct')
  assert.equal(keyStatus('D4', { ...round, result: 'wrong' }), 'wrong')
  assert.equal(keyStatus('E4', { ...round, result: 'wrong' }), 'missed')
  assert.equal(keyStatus('F4', { ...round, result: 'wrong' }), 'idle')
})
