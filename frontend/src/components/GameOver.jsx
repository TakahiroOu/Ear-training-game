export default function GameOver({ t, won, points, mistakes, onPlayAgain }) {
  return (
    <section className="panel game-over">
      <h2 className={won ? 'win' : 'lose'}>{won ? t.win : t.lose}</h2>
      <p>
        {t.points}: {points} · {t.mistakes}: {mistakes}
      </p>
      <button type="button" className="button button-primary" onClick={onPlayAgain}>
        {t.playAgain}
      </button>
    </section>
  )
}
