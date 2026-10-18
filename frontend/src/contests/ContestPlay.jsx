import { useEffect } from 'react'
import Piano from '../components/Piano.jsx'
import { spellNote } from '../game/keys.js'
import { useContestPlay } from './useContestPlay.js'

export default function ContestPlay({ t, token, entry: startEntry, title, onLeaderboard, onBack }) {
  const play = useContestPlay(token, startEntry)
  const { entry, answered } = play
  const tc = t.contest
  const spell = (note) => spellNote(note, null)

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
        {entry.rank && <p>{tc.rankText(entry.rank)}</p>}
        <div className="actions">
          <button type="button" className="button button-primary" onClick={onLeaderboard}>
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
            ? `${answered.result === 'right' ? t.right : answered.result === 'octave' ? t.octave(answered.question_notes.map(spell).join(' ')) : t.wrong(answered.question_notes.map(spell).join(' '))} ${tc.pointsWon(answered.points)}`
            : t.hintListen}
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
    </>
  )
}
