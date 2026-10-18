import { MAX_MISTAKES, WIN_POINTS } from '../game/rules.js'

export default function ScoreBoard({ t, points, mistakes }) {
  return (
    <div className="scoreboard">
      <div className="score score-mistakes">
        {t.mistakes}: {mistakes} / {MAX_MISTAKES}
      </div>
      <div className="score score-points">
        {t.points}: {points} / {WIN_POINTS}
      </div>
    </div>
  )
}
