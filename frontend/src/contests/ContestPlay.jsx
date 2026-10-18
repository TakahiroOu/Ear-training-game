import { useEffect, useState } from 'react'
import Piano from '../components/Piano.jsx'
import { spellNote } from '../game/keys.js'
import { signed } from './format.js'
import { useContestPlay } from './useContestPlay.js'

/** Seconds since the question started, updated a few times per second. */
function useStopwatch(running, resetKey) {
  const [elapsed, setElapsed] = useState({ key: null, seconds: 0 })
  useEffect(() => {
    if (!running) return
    const started = Date.now()
    const timer = setInterval(() => setElapsed({ key: resetKey, seconds: (Date.now() - started) / 1000 }), 100)
    return () => clearInterval(timer)
  }, [running, resetKey])
  // A new question (new resetKey) starts from 0 until the first tick
  return running && elapsed.key === resetKey ? elapsed.seconds : 0
}

export default function ContestPlay({ t, token, entry: startEntry, title, ranked, onPlayAgain, onLeaderboard, onBack }) {
  const play = useContestPlay(token, startEntry)
  const { entry, answered } = play
  const tc = t.contest
  const spell = (note) => spellNote(note, null)
  const seconds = useStopwatch(!answered && !play.busy && !entry.finished, entry.next_index)

  // Shortcuts: Space = replay, Enter = submit / next
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === ' ') {
        event.preventDefault()
        play.replay()
      } else if (event.key === 'Enter') {
        event.preventDefault()
        if (answered) play.next()
        else play.submit()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [play, answered])

  if (entry.finished && !answered) {
    return (
      <section className="panel game-over">
        <h2>{tc.finished}</h2>
        <p className="muted">{title}</p>
        <p className="stat-value">{tc.finalScore(entry.score, entry.correct, entry.question_count)}</p>
        {entry.rank && <p>{ranked ? tc.runRank(entry.rank) : tc.rankText(entry.rank)}</p>}
        <div className="actions">
          {ranked && (
            <button type="button" className="button button-primary" onClick={onPlayAgain}>
              {tc.playAgain}
            </button>
          )}
          <button type="button" className="button" onClick={onLeaderboard}>
            {tc.leaderboard}
          </button>
          <button type="button" className="button" onClick={onBack}>
            {tc.back}
          </button>
        </div>
      </section>
    )
  }

  // While a question is open, the server hasn't told us its notes, so only our own picks are colored
  const questionNumber = answered ? entry.next_index : entry.next_index + 1
  const mode = answered ? answered.question_notes.length : entry.next_mode
  const answerText = answered?.question_notes.map(spell).join(' ')
  const resultText = !answered
    ? null
    : answered.result === 'right'
      ? t.right
      : answered.result === 'octave'
        ? t.octave(answerText)
        : t.wrong(answerText)

  return (
    <>
      <div className="contest-header">
        <span>{title}</span>
        <span>
          {tc.questionOf(questionNumber, entry.question_count)} · {tc.findNotes(mode)}
        </span>
        <span className="score-points">{tc.score(entry.score)}</span>
      </div>

      <div className="actions">
        <button type="button" className="button" disabled={play.busy} onClick={play.replay}>
          <kbd>Space</kbd> {t.replay}
        </button>
        {answered ? (
          <button type="button" className="button button-primary" onClick={play.next}>
            <kbd>Enter</kbd> {tc.next}
          </button>
        ) : (
          <button
            type="button"
            className="button button-primary"
            disabled={play.busy || play.selected.length === 0}
            onClick={play.submit}
          >
            <kbd>Enter</kbd> {tc.submit}
          </button>
        )}
      </div>

      <p className={`message message-${play.error ? 'error' : answered ? answered.result : 'hint'}`} aria-live="polite">
        {play.error
          ? tc.audioError
          : answered
            ? `${resultText} ${tc.pointsAndTime(signed(answered.points), (answered.response_ms / 1000).toFixed(1))}`
            : `${t.hintListen} ${tc.stopwatch(seconds.toFixed(1))}`}
      </p>
      {play.error && (
        <button type="button" className="button" onClick={play.retry}>
          {tc.retry}
        </button>
      )}

      <Piano
        selected={play.selected}
        answer={answered?.question_notes ?? []}
        result={answered?.result ?? null}
        onPress={play.pressKey}
        spell={spell}
      />
      <p className="muted small">{tc.speedRule}</p>
    </>
  )
}
