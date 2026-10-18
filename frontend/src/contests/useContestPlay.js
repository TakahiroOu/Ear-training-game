// Playing one competition attempt. The server sends each question as audio only,
// and grades the answer: the browser learns the notes only after answering.
import { useEffect, useRef, useState } from 'react'
import { answerCompetition, fetchQuestionAudio } from '../api/client.js'
import { playNotes, playResult, prepareClip } from '../audio/sampler.js'

export function useContestPlay(token, startEntry) {
  const [entry, setEntry] = useState(startEntry) // progress: next_index, next_mode, score, finished...
  const [selected, setSelected] = useState([])
  const [answered, setAnswered] = useState(null) // after answering: { result, points, question_notes }
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(false)
  const clip = useRef(null)

  async function loadQuestion() {
    setBusy(true)
    setError(false)
    try {
      const audio = await fetchQuestionAudio(token, entry.id)
      clip.current?.dispose()
      clip.current = await prepareClip(audio)
      clip.current.play()
    } catch {
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  // Load the first question when the attempt opens; free the audio when leaving
  useEffect(() => {
    if (!startEntry.finished) loadQuestion()
    return () => clip.current?.dispose()
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only once, when opening
  }, [])

  function replay() {
    clip.current?.play()
  }

  function pressKey(note) {
    playNotes([note])
    if (answered || entry.finished) return
    setSelected((current) => (current.includes(note) ? current.filter((n) => n !== note) : [...current, note]))
  }

  async function submit() {
    if (answered || busy || selected.length === 0 || !clip.current) return
    setBusy(true)
    try {
      const response = await answerCompetition(token, entry.id, entry.next_index, selected)
      playResult(response.result !== 'wrong')
      setAnswered(response)
      setEntry(response.entry)
    } catch {
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  function next() {
    if (!answered) return
    setAnswered(null)
    setSelected([])
    if (!entry.finished) loadQuestion()
  }

  return { entry, selected, answered, busy, error, replay, pressKey, submit, next, retry: loadQuestion }
}
