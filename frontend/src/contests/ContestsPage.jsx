import { useCallback, useEffect, useState } from 'react'
import {
  closeCompetition,
  createClassCompetition,
  enterCompetition,
  fetchCompetitions,
  findCompetitionByCode,
} from '../api/client.js'
import { loadSounds } from '../audio/sampler.js'
import ContestPlay from './ContestPlay.jsx'
import { contestTitle } from './format.js'
import Leaderboard from './Leaderboard.jsx'
import PlayerNameForm from './PlayerNameForm.jsx'

/** One competition in the list. */
function ContestCard({ t, competition, loggedIn, onPlay, onLeaderboard, onClose }) {
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
          {ranked
            ? `${tc.categoryHint[competition.category]} · ${tc.questions(competition.question_count)}`
            : `${tc.questions(competition.question_count)} · ${competition.active ? tc.open : tc.closed}`}{' '}
          · {tc.entries(competition.entries)}
        </p>
        {competition.join_code && competition.active && <p className="small">{tc.shareCode(competition.join_code)}</p>}
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
        {competition.is_mine && competition.active && (
          <button type="button" className="button" onClick={() => onClose(competition)}>
            {tc.close}
          </button>
        )}
      </div>
    </div>
  )
}

function ClassCompetitionForms({ t, token, onFound, onCreated }) {
  const tc = t.contest
  const [code, setCode] = useState('')
  const [form, setForm] = useState({ title: '', category: 'mixed', question_count: 20 })
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
        question_count: Number(form.question_count), // form values are text
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
        <label>
          {tc.questionsLabel}
          <input
            type="number"
            min={1}
            max={100}
            value={form.question_count}
            onChange={(e) => setForm({ ...form, question_count: e.target.value })}
            required
          />
        </label>
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
  const [view, setView] = useState({ name: 'list' }) // list | name | play | leaderboard
  const [error, setError] = useState(null)

  const reload = useCallback(() => {
    fetchCompetitions(auth.token)
      .then(setLists)
      .catch(() => setError(t.serverError))
  }, [auth.token, t.serverError])

  useEffect(reload, [reload])

  /** Start a run (with the name typed for it), or continue the unfinished one (playerName = null). */
  async function start(competition, playerName = null) {
    setError(null)
    try {
      await loadSounds() // sounds need a click to start: this runs right after one
      const entry = await enterCompetition(auth.token, competition.id, playerName)
      setView({ name: 'play', entry, competition })
    } catch (e) {
      setError(e.detail === 'This competition is not open' ? tc.notOpen : t.serverError)
      setView({ name: 'list' })
    }
  }

  // A new run always asks for its leaderboard name (it can be different every time)
  const askName = (competition) => setView({ name: 'name', competition })
  const play = (competition) => {
    const open = competition.my_entry && !competition.my_entry.finished
    if (open) start(competition)
    else askName(competition)
  }

  async function close(competition) {
    if (!window.confirm(tc.closeConfirm)) return
    try {
      await closeCompetition(auth.token, competition.id)
      reload()
    } catch {
      setError(t.serverError)
    }
  }

  const backToList = () => {
    setView({ name: 'list' })
    reload()
  }
  const showLeaderboard = (competitionId) => setView({ name: 'leaderboard', competitionId })

  if (view.name === 'name') {
    return (
      <PlayerNameForm
        t={t}
        token={auth.token}
        title={contestTitle(t, view.competition)}
        onSubmit={(playerName) => start(view.competition, playerName)}
        onBack={backToList}
      />
    )
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
        onPlayAgain={() => askName(view.competition)}
        onLeaderboard={() => showLeaderboard(view.competition.id)}
        onBack={backToList}
      />
    )
  }
  if (view.name === 'leaderboard') {
    return <Leaderboard t={t} token={auth.token} competitionId={view.competitionId} onBack={backToList} />
  }

  const card = (competition) => (
    <ContestCard
      key={competition.id}
      t={t}
      competition={competition}
      loggedIn={Boolean(auth.user)}
      onPlay={play}
      onLeaderboard={showLeaderboard}
      onClose={close}
    />
  )

  return (
    <section className="panel">
      <h2>{tc.rankedTitle}</h2>
      <p className="muted small">{tc.intro}</p>
      {!auth.user && <p className="message message-info">{tc.loginToPlay}</p>}
      {error && <p className="message message-error">{error}</p>}
      {!lists ? <p className="muted">…</p> : lists.ranked.map(card)}

      <h2 className="section-title">{tc.classesTitle}</h2>
      <p className="muted small">{tc.classesIntro}</p>
      {auth.user && <ClassCompetitionForms t={t} token={auth.token} onFound={setFound} onCreated={reload} />}
      {found && !lists?.classes.some((c) => c.id === found.id) && card(found)}
      {lists?.classes.map(card)}
    </section>
  )
}
