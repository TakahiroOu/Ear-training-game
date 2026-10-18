export default function RulesScreen({ t, loading, error, onStart }) {
  return (
    <section className="panel">
      <h2>{t.rulesTitle}</h2>
      <ul>
        {t.rules.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <h2>{t.scoringTitle}</h2>
      <ul>
        {t.scoring.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <button type="button" className="button button-primary" disabled={loading} onClick={onStart}>
        {loading ? t.loadingSounds : t.start}
      </button>
      {error && <p className="message message-error">{t.soundError}</p>}
    </section>
  )
}
