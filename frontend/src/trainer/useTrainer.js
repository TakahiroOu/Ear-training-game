// The interval & chord trainer's state and actions.
import { useState } from 'react'
import { fetchTrainerQuestion, saveTrainerResult } from '../api/client.js'
import { loadSounds, playMelody, playNotes, playResult } from '../audio/sampler.js'
import { DEFAULT_SETTINGS, TEST_LENGTH, answerComplete, checkTrainerAnswer } from './trainerRules.js'

const STORAGE_KEY = 'trainerSettings'

function loadSettings() {
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') }
  } catch {
    return DEFAULT_SETTINGS // storage blocked or broken: just use the defaults
  }
}

export function useTrainer(auth) {
  const [settings, setSettings] = useState(loadSettings)
  const [phase, setPhase] = useState('settings') // 'settings' | 'quiz' | 'summary'
  const [loading, setLoading] = useState(false)
  const [question, setQuestion] = useState(null) // { notes, answer: { kind, name, inversion, root } }
  const [given, setGiven] = useState({}) // what the player chose: { name, inversion, root }
  const [checked, setChecked] = useState(null) // null until checked, then { correct, parts }
  const [count, setCount] = useState({ asked: 0, correct: 0 })
  const [error, setError] = useState(null) // null | 'nothing' | 'settings' | 'sound' | 'server'
  const [saved, setSaved] = useState(null) // test results: null | 'saved' | 'failed'

  function updateSettings(changes) {
    const next = { ...settings, ...changes }
    setSettings(next)
    setError(null)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    } catch {
      // not remembered, but still used for this visit
    }
  }

  function play(current = question) {
    if (!current) return
    if (settings.playback === 'melodic') playMelody(current.notes, settings.noteLength)
    else playNotes(current.notes, settings.noteLength)
  }

  async function nextQuestion() {
    try {
      const next = await fetchTrainerQuestion(settings)
      setQuestion(next)
      setGiven({})
      setChecked(null)
      setError(null)
      play(next)
    } catch (e) {
      setError(e.status === 422 ? 'settings' : 'server')
      setPhase('settings')
    }
  }

  async function start() {
    if (!settings.intervals.length && !settings.triads.length && !settings.sevenths.length) {
      setError('nothing')
      return
    }
    setLoading(true)
    try {
      await loadSounds() // needs this click: browsers block sound until the user interacts
    } catch {
      setError('sound')
      return
    } finally {
      setLoading(false)
    }
    setCount({ asked: 0, correct: 0 })
    setSaved(null)
    setPhase('quiz')
    await nextQuestion()
  }

  /** Pick part of the answer: choose('name', 'P5'), choose('inversion', 1), choose('root', 'C'). */
  function choose(part, value) {
    if (checked) return
    setGiven((current) => ({ ...current, [part]: value }))
  }

  function check() {
    if (!question || checked || !answerComplete(given, question.answer, settings)) return
    const result = checkTrainerAnswer(given, question.answer, settings)
    playResult(result.correct)
    setChecked(result)
    setCount((current) => ({ asked: current.asked + 1, correct: current.correct + (result.correct ? 1 : 0) }))
  }

  function next() {
    if (!checked) return
    if (settings.mode === 'test' && count.asked >= TEST_LENGTH) finishTest()
    else nextQuestion()
  }

  function finishTest() {
    setPhase('summary')
    if (!auth.token) return
    const { intervals, triads, sevenths, inversions, low, high } = settings
    saveTrainerResult(auth.token, {
      total: count.asked,
      correct: count.correct,
      settings: { intervals, triads, sevenths, inversions, low, high },
    })
      .then(() => setSaved('saved'))
      .catch(() => setSaved('failed'))
  }

  function backToSettings() {
    setPhase('settings')
    setQuestion(null)
    setChecked(null)
  }

  return {
    settings, updateSettings, phase, loading, question, given, checked, count, error, saved,
    start, play, choose, check, next, backToSettings,
  }
}
