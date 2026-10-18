import { useEffect, useState } from 'react'
import { fetchLeaderboard } from '../api/client.js'
import { contestTitle, timeLeft } from './format.js'

export default function Leaderboard({ t, language, token, competitionId, onBack }) {
  const [board, setBoard] = useState(null)
  const [error, setError] = useState(false)
  const tc = t.contest

  useEffect(() => {
    fetchLeaderboard(token, competitionId)
      .then(setBoard)
      .catch(() => setError(true))
  }, [token, competitionId])

  if (error) return <section className="panel message-error">{t.serverError}</section>
  if (!board) return <section className="panel muted">…</section>

  const row = (r) => (
    <tr key={`${r.rank}-${r.name}`} className={r.is_me ? 'row-me' : ''}>
      <td>{r.rank}</td>
      <td>{r.name}</td>
      <td>{r.score}</td>
      <td>{r.correct}</td>
      <td>{tc.seconds(r.total_ms)}</td>
    </tr>
  )

  return (
    <section className="panel">
      <button type="button" className="link" onClick={onBack}>
        ← {tc.back}
      </button>
      <h2>{contestTitle(t, board.competition, language)}</h2>
      <p className="muted">
        {tc.players(board.competition.players)} · {timeLeft(t, board.competition)}
      </p>
      {board.rows.length === 0 ? (
        <p>{tc.noEntries}</p>
      ) : (
        <table className="table leaderboard">
          <thead>
            <tr>
              <th>{tc.rank}</th>
              <th>{tc.name}</th>
              <th>{tc.scoreCol}</th>
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
