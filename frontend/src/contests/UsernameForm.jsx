import { useState } from 'react'
import { setUsername } from '../api/client.js'

/** Asked the first time someone plays a contest or a live room: the name shown to others. */
export default function UsernameForm({ t, token, onSaved }) {
  const [name, setName] = useState('')
  const [error, setError] = useState(null)
  const tc = t.contest

  async function save(event) {
    event.preventDefault()
    try {
      await setUsername(token, name.trim())
      onSaved()
    } catch (e) {
      setError(e.detail === 'username_taken' ? tc.usernameTaken : tc.usernameHint)
    }
  }

  return (
    <section className="panel">
      <h2>{tc.usernameTitle}</h2>
      <form className="form" onSubmit={save}>
        <input value={name} onChange={(e) => setName(e.target.value)} minLength={2} maxLength={20} required autoFocus />
        <p className="muted small">{tc.usernameHint}</p>
        <button type="submit" className="button button-primary">
          {tc.save}
        </button>
      </form>
      {error && <p className="message message-error">{error}</p>}
    </section>
  )
}
