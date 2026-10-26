import { useEffect, useState } from 'react'
import { fetchLeaderboard } from '../api/client.js'
import { contestTitle } from './format.js'

export default function Leaderboard({ t, token, competitionId, onBack }) {
  const [period, setPeriod] = useState('week') // ranked: 'week' or 'all'
  const [board, setBoard] = useState(null)
  const [error, setError] = useState(false)
  const tc = t.contest

  useEffect(() => {
    fetchLeaderboard(token, competitionId, period)
      .then(setBoard)
      .catch(() => setError(true))
  }, [token, competitionId, period])

  if (error) return <section className="panel message-error">{t.serverError}</section>
  if (!board) return <section className="panel muted">…</section>

  const ranked = board.competition.kind === 'ranked'
  const row = (r) => (
    <tr key={`${r.rank}-${r.name}`} className={r.is_me ? 'row-me' : ''}>
      <td>{r.rank}</td>
      <td>{r.name}</td>
      <td>{r.score}</td>
      <td>{tc.correctOf(r.correct, r.question_count)}</td>
      <td>{tc.seconds(r.total_ms)}</td>
    </tr>
  )

  return (
    <section className="panel">
      <button type="button" className="link" onClick={onBack}>
        ← {tc.back}
      </button>
      <h2>{contestTitle(t, board.competition)}</h2>
      <p className="muted">
        {tc.players(board.competition.players)}
        {!ranked && ` · ${board.competition.active ? tc.open : tc.closed}`}
      </p>
      {ranked && <p className="muted small">{tc.rankedRule}</p>}
      {ranked && (
        <div className="choice">
          {['week', 'all'].map((p) => (
            <button
              key={p}
              type="button"
              className={p === period ? 'button button-active' : 'button'}
              onClick={() => setPeriod(p)}
            >
              {tc.periods[p]}
            </button>
          ))}
        </div>
      )}
      {board.rows.length === 0 ? (
        <p>{tc.noEntries}</p>
      ) : (
        <table className="table leaderboard">
          <thead>
            <tr>
              <th>{tc.rank}</th>
              <th>{tc.name}</th>
              <th>{ranked ? tc.bestScoreCol : tc.scoreCol}</th>
              <th>{tc.correctCol}</th>
              <th>{tc.time}</th>
            </tr>
          </thead>
          <tbody>
            {board.rows.map(row)}
            {board.me && !board.rows.some((r) => r.is_me) && row(board.me)}
          </tbody>
        </table>
      )}
    </section>
  )
}
