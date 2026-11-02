import { useEffect, useState } from 'react'
import { fetchAnalytics } from '../api/client.js'

// A result needs this many answers before it can be called "the most missed"
const MIN_ANSWERS = 3

const percent = (share) => Math.round(share * 100)
const seconds = (ms) => (ms == null ? '–' : `${(ms / 1000).toFixed(1)}`)

/** The row with the lowest accuracy among rows with enough answers (null if none). */
function hardest(rows) {
  const enough = rows.filter((row) => row.answers >= MIN_ANSWERS)
  return enough.length ? enough.reduce((worst, row) => (row.accuracy < worst.accuracy ? row : worst)) : null
}

/** Horizontal bars: accuracy of each row, the hardest one in red. */
function Bars({ ta, rows, label, worst }) {
  return rows.map((row) => (
    <div key={label(row)} className="bar-row">
      <span className="bar-label">{label(row)}</span>
      <div className="bar">
        <div
          className={row === worst ? 'bar-fill bar-fill-worst' : 'bar-fill'}
          style={{ width: `${percent(row.accuracy)}%` }}
        />
      </div>
      <span className="bar-value">
        {percent(row.accuracy)}% · {ta.count(row.answers)}
        {row.median_ms != null && ` · ${ta.median(seconds(row.median_ms))}`}
      </span>
    </div>
  ))
}

function Highlight({ ta, title, row, name }) {
  if (!row) return null
  return (
    <div className="stat-tile analytics-highlight">
      <span className="muted small">{title}</span>
      <span className="stat-value lose">{name}</span>
      {ta.accuracyOf(percent(row.accuracy), row.answers)}
    </div>
  )
}

/** Which notes, intervals and chords are missed most: everyone's data, or your own. */
export default function AnalyticsPage({ t, auth }) {
  const ta = t.analytics
  const [scope, setScope] = useState('everyone')
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetchAnalytics(auth.token, scope)
      .then((result) => {
        setData(result)
        setError(false)
      })
      .catch(() => setError(true))
  }, [auth.token, scope])

  const chordName = (quality) => t.trainer.triads[quality] ?? t.trainer.sevenths[quality] ?? quality
  const shown = data?.scope === scope ? data : null // the old data while the new scope loads

  return (
    <section className="panel stats analytics">
      <h2>{ta.title}</h2>
      <p className="muted">{ta.intro}</p>

      {auth.user && (
        <div className="choice">
          {['everyone', 'me'].map((s) => (
            <button
              key={s}
              type="button"
              className={s === scope ? 'button button-active' : 'button'}
              onClick={() => setScope(s)}
            >
              {ta.scopes[s]}
            </button>
          ))}
        </div>
      )}

      {error && <p className="message message-error">{t.serverError}</p>}
      {!error && !shown && <p className="muted">…</p>}
      {shown && shown.answers === 0 && <p>{scope === 'me' ? ta.noDataMe : ta.noData}</p>}

      {shown && shown.answers > 0 && (
        <>
          <p>
            {shown.players != null ? ta.basedOn(shown.answers, shown.players) : ta.basedOnMe(shown.answers)}
          </p>

          <div className="stat-tiles">
            <Highlight
              ta={ta}
              title={ta.hardestInterval}
              row={hardest(shown.intervals)}
              name={hardest(shown.intervals) && t.trainer.intervals[hardest(shown.intervals).interval]}
            />
            <Highlight
              ta={ta}
              title={ta.hardestChord}
              row={hardest(shown.chords)}
              name={hardest(shown.chords) && chordName(hardest(shown.chords).quality)}
            />
            <Highlight ta={ta} title={ta.hardestNote} row={hardest(shown.notes)} name={hardest(shown.notes)?.note} />
          </div>

          {shown.intervals.length > 0 && (
            <>
              <h3>{ta.intervals}</h3>
              <p className="muted small">{ta.intervalsHint}</p>
              <Bars
                ta={ta}
                rows={shown.intervals}
                label={(row) => t.trainer.intervals[row.interval]}
                worst={hardest(shown.intervals)}
              />
            </>
          )}

          {shown.chords.length > 0 && (
            <>
              <h3>{ta.chords}</h3>
              <Bars ta={ta} rows={shown.chords} label={(row) => chordName(row.quality)} worst={hardest(shown.chords)} />
            </>
          )}

          {shown.notes.length > 0 && (
            <>
              <h3>{ta.notes}</h3>
              <Bars ta={ta} rows={shown.notes} label={(row) => row.note} worst={hardest(shown.notes)} />
            </>
          )}

          {shown.confusions.length > 0 && (
            <>
              <h3>{ta.confusions}</h3>
              <p className="muted small">{ta.confusionsHint}</p>
              <table className="table">
                <thead>
                  <tr>
                    <th>{ta.played}</th>
                    <th>{ta.answered}</th>
                    <th>{ta.times}</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.confusions.map((row) => (
                    <tr key={`${row.played}-${row.answered}`}>
                      <td>{row.played}</td>
                      <td>{row.answered}</td>
                      <td>{row.times}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          <h3>{ta.byMode}</h3>
          <Bars ta={ta} rows={shown.by_mode} label={(row) => t.modeButton(row.mode)} worst={null} />
          <p className="muted small">{ta.footnote}</p>
        </>
      )}
    </section>
  )
}
