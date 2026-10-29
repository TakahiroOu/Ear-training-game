/**
 * The first screen: what you can do here (competitions first), a big start button,
 * and the rules folded away under "How to play".
 */
export default function RulesScreen({ t, loading, error, onStart, onOpen }) {
  const th = t.home
  const cards = [
    { icon: '🏆', page: 'contests', ...th.cards.ranked, highlight: true },
    { icon: '⚔️', page: 'friends', ...th.cards.friends, highlight: true },
    { icon: '🎹', page: 'play', ...th.cards.play },
    { icon: '🎧', page: 'trainer', ...th.cards.trainer },
  ]

  return (
    <>
      <section className="home-hero">
        <h2>{th.headline}</h2>
        <p>{th.subline}</p>
        <button type="button" className="button button-primary button-big" disabled={loading} onClick={onStart}>
          {loading ? t.loadingSounds : th.playNow}
        </button>
        {error && <p className="message message-error">{t.soundError}</p>}
      </section>

      <section className="mode-cards">
        {cards.map((card) => (
          <button
            key={card.page}
            type="button"
            className={card.highlight ? 'mode-card mode-card-highlight' : 'mode-card'}
            disabled={card.page === 'play' && loading}
            onClick={() => (card.page === 'play' ? onStart() : onOpen(card.page))}
          >
            <span className="mode-card-icon" aria-hidden="true">
              {card.icon}
            </span>
            <span className="mode-card-title">{card.title}</span>
            <span className="mode-card-text">{card.text}</span>
            <span className="mode-card-go">{card.go} →</span>
          </button>
        ))}
      </section>

      <details className="panel rules-details">
        <summary>{t.rulesTitle}</summary>
        <ul>
          {t.rules.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <h3>{t.scoringTitle}</h3>
        <ul>
          {t.scoring.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </details>
    </>
  )
}
