import { useCallback, useEffect, useState } from 'react'
import {
  createClassCompetition,
  enterCompetition,
  fetchCompetitions,
  fetchMe,
  findCompetitionByCode,
  setUsername,
} from '../api/client.js'
import { loadSounds } from '../audio/sampler.js'
import ContestPlay from './ContestPlay.jsx'
import { contestTitle, timeLeft } from './format.js'
import Leaderboard from './Leaderboard.jsx'

/** One contest in the list. */
function ContestCard({ t, language, competition, loggedIn, onPlay, onLeaderboard }) {
  const tc = t.contest
  const mine = competition.my_entry
  return (
    <div className="contest-card">
      <div>
        <h3>{contestTitle(t, competition, language)}</h3>
        <p className="muted small">
          {tc.questions(competition.question_count)} · {tc.players(competition.players)} · {timeLeft(t, competition)}
        </p>
        {competition.join_code && <p className="small">{tc.shareCode(competition.join_code)}</p>}
        {mine?.finished && <p className="win">{tc.yourResult(mine.score, mine.rank)}</p>}
      </div>
      <div className="contest-buttons">
        {loggedIn && competition.active && !mine?.finished && (
          <button type="button" className="button button-primary" onClick={() => onPlay(competition)}>
            {mine ? tc.continue : tc.play}
          </button>
        )}
        <button type="button" className="button" onClick={() => onLeaderboard(competition.id)}>
          {tc.leaderboard}
        </button>
      </div>
    </div>
  )
}

function UsernameForm({ t, token, onSaved }) {
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

function ClassCompetitions({ t, token, onFound, onCreated }) {
  const tc = t.contest
  const [code, setCode] = useState('')
  const [form, setForm] = useState({ title: '', question_count: 20, days: 7 })
  const [message, setMessage] = useState(null)

  async function join(event) {
    event.preventDefault()
    try {
      onFound(await findCompetitionByCode(token, code))
      setMessage(null)
    } catch {
      setMessage(tc.codeNotFound)
    }
  }

  async function create(event) {
    event.preventDefault()
    try {
      const created = await createClassCompetition(token, { ...form, title: form.title.trim() })
      setMessage(tc.shareCode(created.join_code))
      setForm({ ...form, title: '' })
      onCreated()
    } catch {
      setMessage(t.serverError)
    }
  }

  return (
    <div className="class-forms">
      <form className="inline-form" onSubmit={join}>
        <label>
          {tc.joinCode}
          <input value={code} onChange={(e) => setCode(e.target.value)} maxLength={8} required />
        </label>
        <button type="submit" className="button">
          {tc.join}
        </button>
      </form>
      <form className="inline-form" onSubmit={create}>
        <label>
          {tc.titleLabel}
          <input
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            maxLength={60}
            required
          />
        </label>
        <label>
          {tc.questionsLabel}
          <select value={form.question_count} onChange={(e) => setForm({ ...form, question_count: Number(e.target.value) })}>
            {[8, 12, 20, 30, 40].map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
        <label>
          {tc.daysLabel}
          <select value={form.days} onChange={(e) => setForm({ ...form, days: Number(e.target.value) })}>
            {[1, 3, 7, 14, 30].map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
        <button type="submit" className="button">
          {tc.create}
        </button>
      </form>
      {message && <p className="message message-info">{message}</p>}
    </div>
  )
}

export default function ContestsPage({ t, language, auth }) {
  const tc = t.contest
  const [lists, setLists] = useState(null)
  const [found, setFound] = useState(null) // a class competition found by its join code
  const [view, setView] = useState({ name: 'list' }) // list | username | play | leaderboard
  const [error, setError] = useState(null)

  const reload = useCallback(() => {
    fetchCompetitions(auth.token)
      .then(setLists)
      .catch(() => setError(t.serverError))
  }, [auth.token, t.serverError])

  useEffect(reload, [reload])

  async function play(competition) {
    setError(null)
    try {
      await loadSounds() // this click lets the browser play sound
      const me = await fetchMe(auth.token)
      if (!me.username) {
        setView({ name: 'username', competition })
        return
      }
      const entry = await enterCompetition(auth.token, competition.id)
      setView({ name: 'play', entry, title: contestTitle(t, competition, language), competitionId: competition.id })
    } catch (e) {
      setError(e.detail === 'This competition is not open' ? tc.notOpen : t.serverError)
    }
  }

  const backToList = () => {
    setView({ name: 'list' })
    reload()
  }
  const showLeaderboard = (competitionId) => setView({ name: 'leaderboard', competitionId })

  if (view.name === 'username') {
    return <UsernameForm t={t} token={auth.token} onSaved={() => play(view.competition)} />
  }
  if (view.name === 'play') {
    return (
      <ContestPlay
        t={t}
        token={auth.token}
        entry={view.entry}
        title={view.title}
        onLeaderboard={() => showLeaderboard(view.competitionId)}
        onBack={backToList}
      />
    )
  }
  if (view.name === 'leaderboard') {
    return <Leaderboard t={t} language={language} token={auth.token} competitionId={view.competitionId} onBack={backToList} />
  }

  const card = (competition) => (
    <ContestCard
      key={competition.id}
      t={t}
      language={language}
      competition={competition}
      loggedIn={Boolean(auth.user)}
      onPlay={play}
      onLeaderboard={showLeaderboard}
    />
  )

  return (
    <section className="panel">
      <h2>{tc.title}</h2>
      <p className="muted small">{tc.intro}</p>
      {!auth.user && <p className="message message-info">{tc.loginToPlay}</p>}
      {error && <p className="message message-error">{error}</p>}
      {!lists ? <p className="muted">…</p> : lists.current.map(card)}

      <h2 className="section-title">{tc.classesTitle}</h2>
      <p className="muted small">{tc.classesIntro}</p>
      {auth.user && (
        <ClassCompetitions t={t} token={auth.token} onFound={setFound} onCreated={reload} />
      )}
      {found && !lists?.classes.some((c) => c.id === found.id) && card(found)}
      {lists?.classes.map(card)}
    </section>
  )
}
