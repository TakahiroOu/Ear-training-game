import { useState } from 'react'
import { createRoom } from '../api/client.js'
import UsernameForm from '../contests/UsernameForm.jsx'
import { readyToPlay } from '../contests/readyToPlay.js'
import LiveRoom from './LiveRoom.jsx'

/** Play live with friends: create a room or join one with its code. */
export default function FriendsPage({ t, auth }) {
  const tl = t.live
  const [view, setView] = useState({ name: 'start' }) // start | username | room
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)

  /** getCode: creates a room (host) or returns the typed code (guest). */
  async function openRoom(getCode) {
    setError(null)
    try {
      if (!(await readyToPlay(auth.token))) {
        setView({ name: 'username', then: getCode })
        return
      }
      setView({ name: 'room', code: await getCode() })
    } catch {
      setError(t.serverError)
    }
  }

  if (view.name === 'username') {
    return <UsernameForm t={t} token={auth.token} onSaved={() => openRoom(view.then)} />
  }
  if (view.name === 'room') {
    return <LiveRoom t={t} code={view.code} token={auth.token} onLeave={() => setView({ name: 'start' })} />
  }

  return (
    <section className="panel">
      <h2>{tl.title}</h2>
      <p className="muted small">{tl.intro}</p>
      {!auth.user ? (
        <p className="message message-info">{tl.loginToPlay}</p>
      ) : (
        <div className="friends-start">
          <div className="friends-option">
            <h3>{tl.hostTitle}</h3>
            <p className="muted small">{tl.hostHint}</p>
            <button
              type="button"
              className="button button-primary"
              onClick={() => openRoom(async () => (await createRoom(auth.token)).code)}
            >
              {tl.create}
            </button>
          </div>
          <form
            className="friends-option"
            onSubmit={(event) => {
              event.preventDefault()
              const typed = code.trim().toUpperCase()
              openRoom(async () => typed)
            }}
          >
            <h3>{tl.joinTitle}</h3>
            <p className="muted small">{tl.joinHint}</p>
            <div className="inline-form">
              <label>
                {tl.roomCode}
                <input value={code} onChange={(e) => setCode(e.target.value)} maxLength={8} required />
              </label>
              <button type="submit" className="button">
                {tl.join}
              </button>
            </div>
          </form>
        </div>
      )}
      {error && <p className="message message-error">{error}</p>}
    </section>
  )
}
