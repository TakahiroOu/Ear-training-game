import { useEffect, useState } from 'react'
import { fetchMe } from '../api/client.js'

const STORAGE_KEY = 'contestPlayerName'

function lastName() {
  try {
    return localStorage.getItem(STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

/** Asked before every new contest run: the name shown on the leaderboard for this run (any name, any time). */
export default function PlayerNameForm({ t, token, title, onSubmit, onBack }) {
  const tc = t.contest
  const [name, setName] = useState(lastName)

  // First time: suggest the account's username
  useEffect(() => {
    if (name) return
    fetchMe(token)
      .then((me) => setName((current) => current || me.username || ''))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only when opening
  }, [])

  function submit(event) {
    event.preventDefault()
    const chosen = name.trim()
    if (!chosen) return
    try {
      localStorage.setItem(STORAGE_KEY, chosen)
    } catch {
      // private window: the name just isn't remembered
    }
    onSubmit(chosen)
  }

  return (
    <section className="panel">
      <button type="button" className="link" onClick={onBack}>
        ← {tc.back}
      </button>
      <h2>{tc.runNameTitle}</h2>
      <p className="muted">{title}</p>
      <form className="form" onSubmit={submit}>
        <input value={name} onChange={(e) => setName(e.target.value)} maxLength={20} required autoFocus />
        <p className="muted small">{tc.runNameHint}</p>
        <button type="submit" className="button button-primary">
          {t.start}
        </button>
      </form>
    </section>
  )
}
