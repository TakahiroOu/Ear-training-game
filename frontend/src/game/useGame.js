// The game's state and actions (replaces class Game from legacy/main.py).
// React re-draws the screen automatically whenever one of these values changes,
// so there's no main_loop.
import { useState } from 'react'
import { fetchQuestion } from '../api/client.js'
import { loadSounds, playNotes, playResult } from '../audio/sampler.js'
import { MAX_MISTAKES, WIN_POINTS, isCorrect, mistakesFor, pointsFor } from './rules.js'

const SHOW_RESULT_BEFORE_END_MS = 1500

export function useGame() {
  const [screen, setScreen] = useState('rules') // 'rules' | 'playing' | 'won' | 'lost'
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState(null) // how many notes the current question has
  const [answer, setAnswer] = useState([]) // notes the server played
  const [selected, setSelected] = useState([]) // notes the player picked
  const [result, setResult] = useState(null) // null until checked, then 'right' | 'wrong'
  const [points, setPoints] = useState(0)
  const [mistakes, setMistakes] = useState(0)
  const [error, setError] = useState(false)

  const hasQuestion = answer.length > 0
  const gameOver = points >= WIN_POINTS || mistakes >= MAX_MISTAKES

  async function start() {
    setLoading(true)
    setError(false)
    try {
      await loadSounds()
      setScreen('playing')
    } catch {
      setError(true) // e.g. a sound file is missing: show a message instead of loading forever
    } finally {
      setLoading(false)
    }
  }

  async function newQuestion(nextMode) {
    if (gameOver) return
    try {
      const notes = await fetchQuestion(nextMode)
      setError(false)
      setMode(nextMode)
      setAnswer(notes)
      setSelected([])
      setResult(null)
      playNotes(notes)
    } catch {
      setError(true)
    }
  }

  /** A piano key was pressed: always play it, and pick/unpick it while answering. */
  function pressKey(note) {
    playNotes([note])
    if (!hasQuestion || result) return
    setSelected((current) =>
      current.includes(note) ? current.filter((n) => n !== note) : [...current, note],
    )
  }

  function replay() {
    if (hasQuestion) playNotes(answer)
  }

  function check() {
    // Fixes from the pygame version: you can't check before a question is played,
    // with nothing picked, or score the same question twice.
    if (!hasQuestion || result || selected.length === 0) return

    const correct = isCorrect(selected, answer)
    playResult(correct)
    setResult(correct ? 'right' : 'wrong')

    if (correct) {
      const newPoints = points + pointsFor(mode)
      setPoints(newPoints)
      if (newPoints >= WIN_POINTS) endGame('won')
    } else {
      const newMistakes = mistakes + mistakesFor(mode)
      setMistakes(newMistakes)
      if (newMistakes >= MAX_MISTAKES) endGame('lost')
    }
  }

  function endGame(finalScreen) {
    // Wait a moment so the player sees the colored keys first.
    setTimeout(() => setScreen(finalScreen), SHOW_RESULT_BEFORE_END_MS)
  }

  function playAgain() {
    setMode(null)
    setAnswer([])
    setSelected([])
    setResult(null)
    setPoints(0)
    setMistakes(0)
    setError(false)
    setScreen('playing')
  }

  return {
    screen, loading, mode, answer, selected, result, points, mistakes, error, hasQuestion,
    start, newQuestion, pressKey, replay, check, playAgain,
  }
}
