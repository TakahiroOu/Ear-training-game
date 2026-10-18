import { useEffect, useState } from 'react'
import { useAuth } from './auth/useAuth.js'
import AccountPage from './components/AccountPage.jsx'
import GameOver from './components/GameOver.jsx'
import KeySelector from './components/KeySelector.jsx'
import ModeSelector from './components/ModeSelector.jsx'
import Piano from './components/Piano.jsx'
import RulesScreen from './components/RulesScreen.jsx'
import ScoreBoard from './components/ScoreBoard.jsx'
import StatsPage from './components/StatsPage.jsx'
import { spellNote } from './game/keys.js'
import { useGame } from './game/useGame.js'
import { LANGUAGES, useLanguage } from './i18n/index.js'

function App() {
  const auth = useAuth()
  const game = useGame({ token: auth.token, userId: auth.user?.id ?? null })
  const { t, language, setLanguage } = useLanguage()
  const [page, setPage] = useState('play') // 'play' | 'stats' | 'account'

  // Keyboard shortcuts, same as the pygame version: 1-4, Enter, Space.
  useEffect(() => {
    if (page !== 'play' || game.screen !== 'playing') return

    function onKeyDown(event) {
      if (['1', '2', '3', '4'].includes(event.key)) {
        game.newQuestion(Number(event.key))
      } else if (event.key === 'Enter') {
        event.preventDefault() // don't also "click" a focused button
        game.check()
      } else if (event.key === ' ') {
        event.preventDefault() // don't scroll the page
        game.replay()
      } else if (event.key === 'k' || event.key === 'K') {
        game.hearKey()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [game, page])

  // Note names as written in the key of the current question (e.g. B♭ in F major)
  const spell = (note) => spellNote(note, game.questionKey ?? game.key)
  const answerText = game.answer.map(spell).join(' ')

  const navButton = (target, label) => (
    <button
      type="button"
      className={page === target ? 'link link-active' : 'link'}
      onClick={() => setPage(target)}
    >
      {label}
    </button>
  )

  return (
    <main className="app">
      <header className="header">
        <h1>{t.title}</h1>
        <nav className="nav">
          {navButton('play', t.play)}
          {auth.user && navButton('stats', t.stats)}
          {auth.enabled && navButton('account', auth.user ? t.account : t.logIn)}
          <span className="nav-divider" />
          {Object.entries(LANGUAGES).map(([code, texts]) => (
            <button
              key={code}
              type="button"
              className={code === language ? 'link link-active' : 'link'}
              onClick={() => setLanguage(code)}
            >
              {texts.languageName}
            </button>
          ))}
        </nav>
      </header>

      {page === 'account' && <AccountPage t={t} auth={auth} onLoggedIn={() => setPage('play')} />}
      {page === 'stats' && auth.token && <StatsPage t={t} token={auth.token} />}

      {page === 'play' && game.screen === 'rules' && (
        <RulesScreen t={t} loading={game.loading} error={game.error} onStart={game.start} />
      )}

      {page === 'play' && game.screen === 'playing' && (
        <>
          <ScoreBoard t={t} points={game.points} mistakes={game.mistakes} />
          <KeySelector
            t={t}
            language={language}
            value={game.key}
            onChange={game.setKey}
            onHearKey={game.hearKey}
          />
          <ModeSelector t={t} currentMode={game.mode} onChoose={game.newQuestion} />

          <div className="actions">
            <button type="button" className="button" disabled={!game.hasQuestion} onClick={game.replay}>
              <kbd>Space</kbd> {t.replay}
            </button>
            <button
              type="button"
              className="button button-primary"
              disabled={!game.hasQuestion || game.result !== null || game.selected.length === 0}
              onClick={game.check}
            >
              <kbd>Enter</kbd> {t.check}
            </button>
          </div>

          <p className={`message message-${game.error ? 'error' : game.result ?? 'hint'}`} aria-live="polite">
            {game.error
              ? t.serverError
              : game.result === 'right'
                ? `${t.right} ${t.next}`
                : game.result === 'octave'
                  ? `${t.octave(answerText)} ${t.next}`
                  : game.result === 'wrong'
                  ? `${t.wrong(answerText)} ${t.next}`
                  : game.hasQuestion
                    ? t.hintListen
                    : t.hintChooseMode}
          </p>

          <Piano
            selected={game.selected}
            answer={game.answer}
            result={game.result}
            onPress={game.pressKey}
            spell={spell}
          />

          {game.saveFailed && <p className="message message-error">{t.saveFailed}</p>}
          {auth.enabled && !auth.user && <p className="muted small">{t.guestNote}</p>}
        </>
      )}

      {page === 'play' && (game.screen === 'won' || game.screen === 'lost') && (
        <GameOver
          t={t}
          won={game.screen === 'won'}
          points={game.points}
          mistakes={game.mistakes}
          onPlayAgain={game.playAgain}
        />
      )}
    </main>
  )
}

export default App
