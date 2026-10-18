// The game's state and actions (replaces class Game from legacy/main.py).
// React re-draws the screen automatically whenever one of these values changes,
// so there's no main_loop.
import { useRef, useState } from 'react'
import { fetchQuestion, saveAnswer, startSession } from '../api/client.js'
import { loadSounds, playNotes, playResult } from '../audio/sampler.js'
import { tonicChord } from './keys.js'
import { MAX_MISTAKES, WIN_POINTS, classifyAnswer, halfPointsFor, mistakesFor, pointsFor } from './rules.js'

const SHOW_RESULT_BEFORE_END_MS = 1500
const KEY_CHORD_BEFORE_QUESTION_MS = 1500

/**
 * `auth` is { token, userId } of the logged-in player, or nulls for guests.
 * Guests play exactly the same; their games just aren't saved.
 */
export function useGame(auth) {
  const [screen, setScreen] = useState('rules') // 'rules' | 'playing' | 'won' | 'lost'
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState(null) // how many notes the current question has
  const [answer, setAnswer] = useState([]) // notes the server played
  const [selected, setSelected] = useState([]) // notes the player picked
  const [result, setResult] = useState(null) // null until checked, then 'right' | 'octave' | 'wrong'
  const [key, setKey] = useState(null) // chosen key (調性) like 'D-major', or null for all 12 notes
  const [questionKey, setQuestionKey] = useState(null) // the key the current question was made in
  const [points, setPoints] = useState(0)
  const [mistakes, setMistakes] = useState(0)
  const [error, setError] = useState(false)
  const [saveFailed, setSaveFailed] = useState(false)

  // Not shown on screen, so kept in refs (changing a ref doesn't redraw the page)
  const savedGame = useRef(null) // { userId, id: Promise<session id> | null } of the game being saved
  const questionStartedAt = useRef(0)
  const keyHeard = useRef(null) // the last key whose tonic chord was played

  const hasQuestion = answer.length > 0
  const gameOver = points >= WIN_POINTS || mistakes >= MAX_MISTAKES

  async function start() {
    setLoading(true)
    setError(false)
    try {
      await loadSounds()
      beginSaving()
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
      const notes = await fetchQuestion(nextMode, key)
      setError(false)
      setMode(nextMode)
      setAnswer(notes)
      setQuestionKey(key)
      setSelected([])
      setResult(null)

      const playQuestion = () => {
        playNotes(notes)
        questionStartedAt.current = Date.now()
      }
      if (key && keyHeard.current !== key) {
        // New key: play its tonic chord first, so the player hears the key
        hearKey()
        setTimeout(playQuestion, KEY_CHORD_BEFORE_QUESTION_MS)
      } else {
        playQuestion()
      }
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

  /** Play the tonic chord of the chosen key. */
  function hearKey() {
    if (!key) return
    playNotes(tonicChord(key))
    keyHeard.current = key
  }

  function check() {
    // Fixes from the pygame version: you can't check before a question is played,
    // with nothing picked, or score the same question twice.
    if (!hasQuestion || result || selected.length === 0) return

    const checked = classifyAnswer(selected, answer)
    playResult(checked !== 'wrong')
    setResult(checked)
    save({
      mode,
      key: questionKey,
      question_notes: answer,
      given_notes: selected,
      response_ms: Date.now() - questionStartedAt.current,
    })

    if (checked === 'right' || checked === 'octave') {
      // Wrong octave: half the points, but no mistakes
      const newPoints = points + (checked === 'right' ? pointsFor(mode) : halfPointsFor(mode))
      setPoints(newPoints)
      if (newPoints >= WIN_POINTS) endGame('won')
    } else {
      const newMistakes = mistakes + mistakesFor(mode)
      setMistakes(newMistakes)
      if (newMistakes >= MAX_MISTAKES) endGame('lost')
    }
  }

  /** A game is saved only if the player was logged in when it started, so saved scores match the screen. */
  function beginSaving() {
    savedGame.current = auth.token ? { userId: auth.userId, id: null } : null
  }

  /** Logged-in players: save the checked question (in the background, the game doesn't wait). */
  function save(checkedAnswer) {
    // Stop saving if the player logged out or someone else logged in during the game
    if (!savedGame.current || !auth.token || savedGame.current.userId !== auth.userId) return
    const token = auth.token
    savedGame.current.id ??= startSession(token) // the first answer creates the saved game
    savedGame.current.id
      .then((id) => saveAnswer(token, id, checkedAnswer))
      .then(() => setSaveFailed(false))
      .catch(() => setSaveFailed(true))
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
    setSaveFailed(false)
    beginSaving()
    setScreen('playing')
  }

  return {
    screen, loading, mode, answer, selected, result, points, mistakes, error, saveFailed, hasQuestion,
    key, questionKey, setKey,
    start, newQuestion, pressKey, replay, hearKey, check, playAgain,
  }
}
