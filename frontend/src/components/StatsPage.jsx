import { useEffect, useState } from 'react'
import { fetchStats } from '../api/client.js'

const percent = (part, whole) => (whole ? Math.round((part / whole) * 100) : 0)

/** The logged-in player's saved progress (data from GET /api/me/stats). */
export default function StatsPage({ t, token }) {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetchStats(token)
      .then(setStats)
      .catch(() => setError(true))
  }, [token])

  if (error) return <section className="panel message-error">{t.statsError}</section>
  if (!stats) return <section className="panel muted">…</section>
  if (stats.games_played === 0) return <section className="panel">{t.noStats}</section>

  return (
    <section className="panel stats">
      <h2>{t.statsTitle}</h2>
      <div className="stat-tiles">
        <div className="stat-tile">
          <span className="stat-value">{stats.games_played}</span>
          {t.gamesPlayed}
        </div>
        <div className="stat-tile">
          <span className="stat-value win">{stats.wins}</span>
          {t.wins}
        </div>
        <div className="stat-tile">
          <span className="stat-value lose">{stats.losses}</span>
          {t.losses}
        </div>
      </div>

      <h3>{t.accuracyByMode}</h3>
      {stats.by_mode.map(({ mode, answered, correct, octave }) => (
        <div key={mode} className="bar-row">
          <span className="bar-label">{t.modeButton(mode)}</span>
          <div className="bar">
            <div className="bar-fill" style={{ width: `${percent(correct, answered)}%` }} />
          </div>
          <span className="bar-value">
            {percent(correct, answered)}% ({correct}/{answered})
            {octave > 0 && ` · ${t.octaveShort} ${octave}`}
          </span>
        </div>
      ))}

      {stats.most_missed_notes.length > 0 && (
        <>
          <h3>{t.mostMissed}</h3>
          <p>
            {stats.most_missed_notes.map(({ note, missed }) => (
              <span key={note} className="chip">
                {note} × {missed}
              </span>
            ))}
          </p>
        </>
      )}

      <h3>{t.recentGames}</h3>
      <table className="table">
        <tbody>
          {stats.recent_sessions.map((game) => (
            <tr key={game.id}>
              <td>{new Date(game.started_at + 'Z').toLocaleString()}</td>
              <td className={game.result === 'won' ? 'win' : game.result === 'lost' ? 'lose' : 'muted'}>
                {game.result === 'won' ? t.resultWon : game.result === 'lost' ? t.resultLost : t.resultUnfinished}
              </td>
              <td>
                {t.points} {game.points} · {t.mistakes} {game.mistakes}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
