// Run with: npm test   (uses Node's built-in test runner, no extra library needed)
import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  BLACK_NOTES,
  WHITE_NOTES,
  classifyAnswer,
  halfPointsFor,
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

test('wrong octave is told apart from a wrong note', () => {
  assert.equal(classifyAnswer(['G4', 'C4', 'E4'], ['C4', 'E4', 'G4']), 'right')
  assert.equal(classifyAnswer(['C5', 'E4', 'G4'], ['C4', 'E4', 'G4']), 'octave')
  assert.equal(classifyAnswer(['C#4'], ['C4']), 'wrong')
  assert.equal(classifyAnswer(['C4', 'E4'], ['C4', 'E4', 'G4']), 'wrong')
  assert.deepEqual([1, 2, 3, 4].map(halfPointsFor), [0, 1, 1, 2])
  assert.equal(keyStatus('C5', { selected: ['C5'], answer: ['C4'], result: 'octave' }), 'octave')
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
