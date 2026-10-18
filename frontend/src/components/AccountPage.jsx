import { useState } from 'react'

/** Log in, create an account, or log out. Supabase handles the passwords. */
export default function AccountPage({ t, auth, onLoggedIn }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState(null) // { kind: 'error' | 'info', text }

  if (!auth.enabled) {
    return <section className="panel">{t.accountsNotReady}</section>
  }

  if (auth.user) {
    return (
      <section className="panel">
        <p>{t.loggedInAs(auth.user.email)}</p>
        <button type="button" className="button" onClick={auth.logOut}>
          {t.logOut}
        </button>
      </section>
    )
  }

  async function submit(action) {
    setBusy(true)
    setMessage(null)
    try {
      if (action === 'signUp') {
        const { needsConfirmation } = await auth.signUp(email, password)
        if (needsConfirmation) setMessage({ kind: 'info', text: t.checkEmail })
        else onLoggedIn()
      } else {
        await auth.logIn(email, password)
        onLoggedIn()
      }
    } catch (error) {
      setMessage({ kind: 'error', text: t.authError(error.message) })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel">
      <h2>{t.accountTitle}</h2>
      <p className="muted">{t.accountWhy}</p>
      <form
        className="form"
        onSubmit={(event) => {
          event.preventDefault() // pressing Enter in the form logs in
          submit('logIn')
        }}
      >
        <label>
          {t.email}
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          {t.password}
          <input
            type="password"
            autoComplete="current-password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <div className="actions">
          <button type="submit" className="button button-primary" disabled={busy}>
            {t.logIn}
          </button>
          <button
            type="button"
            className="button"
            disabled={busy}
            onClick={(event) => event.currentTarget.form.reportValidity() && submit('signUp')}
          >
            {t.signUp}
          </button>
        </div>
      </form>
      {message && <p className={`message message-${message.kind}`}>{message.text}</p>}
    </section>
  )
}
