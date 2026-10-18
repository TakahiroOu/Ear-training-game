import { useCallback, useEffect, useState } from 'react'
import {
  createClassCompetition,
  createRoom,
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
import LiveRoom from './LiveRoom.jsx'

/** One competition in the list. */
function ContestCard({ t, competition, loggedIn, onPlay, onLeaderboard }) {
  const tc = t.contest
  const ranked = competition.kind === 'ranked'
  const best = competition.my_best
  const open = competition.my_entry && !competition.my_entry.finished
  const canPlay = loggedIn && competition.active && (ranked || !best)
  return (
    <div className="contest-card">
      <div>
        <h3>{contestTitle(t, competition)}</h3>
        <p className="muted small">
          {ranked ? tc.categoryHint[competition.category] : timeLeft(t, competition)} ·{' '}
          {tc.questions(competition.question_count)} · {tc.players(competition.players)}
        </p>
        {competition.join_code && <p className="small">{tc.shareCode(competition.join_code)}</p>}
        {best && <p className="win">{ranked ? tc.yourBest(best.score, best.rank) : tc.yourResult(best.score, best.rank)}</p>}
      </div>
      <div className="contest-buttons">
        {canPlay && (
          <button type="button" className="button button-primary" onClick={() => onPlay(competition)}>
            {open ? tc.continue : tc.play}
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

function LiveRoomForms({ t, onCreate, onJoin }) {
  const tl = t.live
  const [code, setCode] = useState('')
  return (
    <div className="class-forms">
      <div className="inline-form">
        <button type="button" className="button button-primary" onClick={onCreate}>
          {tl.create}
        </button>
      </div>
      <form
        className="inline-form"
        onSubmit={(event) => {
          event.preventDefault()
          onJoin(code.trim().toUpperCase())
        }}
      >
        <label>
          {tl.roomCode}
          <input value={code} onChange={(e) => setCode(e.target.value)} maxLength={8} required />
        </label>
        <button type="submit" className="button">
          {tl.join}
        </button>
      </form>
    </div>
  )
}

function ClassCompetitionForms({ t, token, onFound, onCreated }) {
  const tc = t.contest
  const [code, setCode] = useState('')
  const [form, setForm] = useState({ title: '', category: 'mixed', question_count: 20, days: 7 })
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
      const created = await createClassCompetition(token, {
        ...form,
        title: form.title.trim(),
        question_count: Number(form.question_count), // <select> values are text
        days: Number(form.days),
      })
      setMessage(tc.shareCode(created.join_code))
      setForm({ ...form, title: '' })
      onCreated()
    } catch {
      setMessage(t.serverError)
    }
  }

  const select = (field, options, label) => (
    <label>
      {label}
      <select value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })}>
        {options.map(([value, text]) => (
          <option key={value} value={value}>
            {text}
          </option>
        ))}
      </select>
    </label>
  )

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
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} maxLength={60} required />
        </label>
        {select('category', [['easy', tc.categories.easy], ['mixed', tc.categories.mixed]], tc.categoryLabel)}
        {select('question_count', [8, 12, 20, 30, 40].map((n) => [n, n]), tc.questionsLabel)}
        {select('days', [1, 3, 7, 14, 30].map((n) => [n, n]), tc.daysLabel)}
        <button type="submit" className="button">
          {tc.create}
        </button>
      </form>
      {message && <p className="message message-info">{message}</p>}
    </div>
  )
}

export default function ContestsPage({ t, auth }) {
  const tc = t.contest
  const [lists, setLists] = useState(null)
  const [found, setFound] = useState(null) // a class competition found by its join code
  const [view, setView] = useState({ name: 'list' }) // list | username | play | leaderboard | room
  const [error, setError] = useState(null)

  const reload = useCallback(() => {
    fetchCompetitions(auth.token)
      .then(setLists)
      .catch(() => setError(t.serverError))
  }, [auth.token, t.serverError])

  useEffect(reload, [reload])

  /** Sounds need a click to start, and contests need a leaderboard name. Then `next()` runs. */
  async function prepare(next) {
    setError(null)
    try {
      await loadSounds()
      const me = await fetchMe(auth.token)
      if (!me.username) {
        setView({ name: 'username', then: next })
        return
      }
      await next()
    } catch (e) {
      setError(e.detail === 'This competition is not open' ? tc.notOpen : t.serverError)
    }
  }

  const play = (competition) =>
    prepare(async () => {
      const entry = await enterCompetition(auth.token, competition.id)
      setView({ name: 'play', entry, competition })
    })

  const openRoom = (getCode) =>
    prepare(async () => {
      setView({ name: 'room', code: await getCode() })
    })

  const backToList = () => {
    setView({ name: 'list' })
    reload()
  }
  const showLeaderboard = (competitionId) => setView({ name: 'leaderboard', competitionId })

  if (view.name === 'username') {
    return <UsernameForm t={t} token={auth.token} onSaved={() => prepare(view.then)} />
  }
  if (view.name === 'play') {
    return (
      <ContestPlay
        key={view.entry.id}
        t={t}
        token={auth.token}
        entry={view.entry}
        title={contestTitle(t, view.competition)}
        ranked={view.competition.kind === 'ranked'}
        onPlayAgain={() => play(view.competition)}
        onLeaderboard={() => showLeaderboard(view.competition.id)}
        onBack={backToList}
      />
    )
  }
  if (view.name === 'leaderboard') {
    return <Leaderboard t={t} token={auth.token} competitionId={view.competitionId} onBack={backToList} />
  }
  if (view.name === 'room') {
    return <LiveRoom t={t} code={view.code} token={auth.token} onLeave={backToList} />
  }

  const card = (competition) => (
    <ContestCard
      key={competition.id}
      t={t}
      competition={competition}
      loggedIn={Boolean(auth.user)}
      onPlay={play}
      onLeaderboard={showLeaderboard}
    />
  )

  return (
    <section className="panel">
      <h2>{tc.rankedTitle}</h2>
      <p className="muted small">{tc.intro}</p>
      {!auth.user && <p className="message message-info">{tc.loginToPlay}</p>}
      {error && <p className="message message-error">{error}</p>}
      {!lists ? <p className="muted">…</p> : lists.ranked.map(card)}

      <h2 className="section-title">{t.live.title}</h2>
      <p className="muted small">{t.live.intro}</p>
      {auth.user && (
        <LiveRoomForms
          t={t}
          onCreate={() => openRoom(async () => (await createRoom(auth.token)).code)}
          onJoin={(code) => openRoom(async () => code)}
        />
      )}

      <h2 className="section-title">{tc.classesTitle}</h2>
      <p className="muted small">{tc.classesIntro}</p>
      {auth.user && <ClassCompetitionForms t={t} token={auth.token} onFound={setFound} onCreated={reload} />}
      {found && !lists?.classes.some((c) => c.id === found.id) && card(found)}
      {lists?.classes.map(card)}
    </section>
  )
}
