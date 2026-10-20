import { useEffect, useState } from 'react'
import Piano from '../components/Piano.jsx'
import ShareButtons from '../components/ShareButtons.jsx'
import { spellNote } from '../game/keys.js'
import { signed } from '../contests/format.js'
import { useRoom } from './useRoom.js'

const TARGETS = [500, 1000, 2000, 3000]
const MEDALS = ['🥇', '🥈', '🥉']

/** Seconds left to answer, counting down. */
function useCountdown(question, running) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => setNow(Date.now()), 200)
    return () => clearInterval(timer)
  }, [running])
  if (!question) return 0
  return Math.max(0, Math.ceil(question.seconds - (Math.max(now, question.receivedAt) - question.receivedAt) / 1000))
}

export default function LiveRoom({ t, code, token, onLeave }) {
  const live = useRoom(code, token)
  const { room, me, question, reveal, standings } = live
  const tl = t.live
  const spell = (note) => spellNote(note, null)
  const nameOf = (id) => room?.players.find((p) => p.id === id)?.name ?? '?'
  const countdown = useCountdown(question, room?.state === 'question')

  useEffect(() => {
    function onKeyDown(event) {
      if (event.target.tagName === 'SELECT') return
      if (event.key === ' ') {
        event.preventDefault()
        live.replay()
      } else if (event.key === 'Enter') {
        event.preventDefault()
        live.submit()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [live])

  if (live.error && (!room || ['room_not_found', 'room_full', 'game_running', 'not_logged_in', 'username_required', 'disconnected'].includes(live.error))) {
    return (
      <section className="panel">
        <p className="message message-error">{tl.errors[live.error] ?? live.error}</p>
        <button type="button" className="button" onClick={onLeave}>
          {t.contest.back}
        </button>
      </section>
    )
  }
  if (!room) return <section className="panel muted">…</section>

  const scoreboard = (
    <ol className="live-scores">
      {room.players.map((p) => (
        <li key={p.id} className={p.id === me ? 'row-me' : p.connected ? '' : 'muted'}>
          <span>
            {p.name}
            {p.id === room.host && ' ★'}
            {room.state === 'question' && room.answered.includes(p.id) && ' ✓'}
          </span>
          <span>{p.score}</span>
        </li>
      ))}
    </ol>
  )

  // ---------- final ranking ----------
  if (room.state === 'finished') {
    const finalOrder = standings ?? room.players.map((p) => ({ player: p.id, name: p.name, score: p.score }))
    const myIndex = finalOrder.findIndex((s) => s.player === me)
    const myPlace = myIndex >= 0 ? { rank: myIndex + 1, score: finalOrder[myIndex].score } : null
    return (
      <section className="panel game-over">
        <h2>{tl.finished}</h2>
        <ol className="live-scores standings">
          {finalOrder.map((s, i) => (
            <li key={s.player} className={s.player === me ? 'row-me' : ''}>
              <span>
                {MEDALS[i] ?? `${i + 1}.`} {s.name}
              </span>
              <span>{s.score}</span>
            </li>
          ))}
        </ol>
        <div className="actions">
          {live.isHost && (
            <button type="button" className="button button-primary" onClick={live.start}>
              {tl.playAgain}
            </button>
          )}
          <button type="button" className="button" onClick={onLeave}>
            {tl.leave}
          </button>
        </div>
        {live.error && <p className="message message-error">{tl.errors[live.error] ?? live.error}</p>}
        {myPlace && <ShareButtons t={t} text={t.share.live(myPlace.rank, room.players.length, myPlace.score)} />}
      </section>
    )
  }

  // ---------- lobby ----------
  if (room.state === 'lobby') {
    return (
      <section className="panel">
        <h2>{tl.lobbyTitle}</h2>
        <p className="room-code">{room.code}</p>
        <p className="muted small">{tl.shareHint}</p>
        {scoreboard}
        {live.isHost ? (
          <div className="host-settings">
            <label>
              {tl.category}
              <select value={room.category} onChange={(e) => live.configure(e.target.value, room.target)}>
                <option value="easy">{t.contest.categories.easy}</option>
                <option value="mixed">{t.contest.categories.mixed}</option>
              </select>
            </label>
            <label>
              {tl.target}
              <select value={room.target} onChange={(e) => live.configure(room.category, Number(e.target.value))}>
                {TARGETS.map((n) => (
                  <option key={n} value={n}>
                    {tl.points(n)}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="button button-primary"
              disabled={room.players.length < 2}
              onClick={() => {
                live.clearError()
                live.start()
              }}
            >
              {tl.start}
            </button>
          </div>
        ) : (
          <p>{tl.waitingForHost(t.contest.categories[room.category], room.target)}</p>
        )}
        {room.players.length < 2 && <p className="muted small">{tl.needTwo}</p>}
        <p className="muted small">{tl.rules}</p>
        {live.error && <p className="message message-error">{tl.errors[live.error] ?? live.error}</p>}
        <button type="button" className="link" onClick={onLeave}>
          {tl.leave}
        </button>
      </section>
    )
  }

  // ---------- playing: question or reveal ----------
  const lastFeed = live.feed.map((e) => (
    <li key={`${e.kind}-${e.player}`} className={e.kind === 'correct' ? 'win' : 'lose'}>
      {e.kind === 'correct'
        ? tl.gotIt(nameOf(e.player), e.rank, signed(e.points))
        : e.octave
          ? tl.octaveOff(nameOf(e.player))
          : tl.wrongAnswer(nameOf(e.player), signed(e.points))}
    </li>
  ))

  return (
    <div className="live-layout">
      <div>
        <div className="contest-header">
          <span>{tl.roundOf(room.round, room.target)}</span>
          <span>{question && t.contest.findNotes(question.mode)}</span>
          {room.state === 'question' && <span className="score-mistakes">{tl.secondsLeft(countdown)}</span>}
        </div>
        <div className="actions">
          <button type="button" className="button" onClick={live.replay}>
            <kbd>Space</kbd> {t.replay}
          </button>
          <button
            type="button"
            className="button button-primary"
            disabled={!live.canAnswer || live.selected.length === 0}
            onClick={live.submit}
          >
            <kbd>Enter</kbd> {t.contest.submit}
          </button>
        </div>
        <p className="message message-hint" aria-live="polite">
          {reveal
            ? tl.answerWas(reveal.notes.map(spell).join(' '))
            : live.answeredAlready
              ? tl.waitOthers
              : tl.scorers(room.scorers_allowed)}
        </p>
        <Piano
          selected={live.selected}
          answer={reveal?.notes ?? []}
          result={reveal ? 'shown' : null}
          onPress={live.pressKey}
          spell={spell}
        />
        <ul className="feed">{lastFeed}</ul>
      </div>
      <aside>
        <h3>{tl.scoresTitle}</h3>
        {scoreboard}
        {live.isHost && (
          <button type="button" className="link" onClick={live.end}>
            {tl.endGame}
          </button>
        )}
      </aside>
    </div>
  )
}
