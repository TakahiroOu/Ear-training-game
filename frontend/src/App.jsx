import { useEffect } from 'react'
import GameOver from './components/GameOver.jsx'
import ModeSelector from './components/ModeSelector.jsx'
import Piano from './components/Piano.jsx'
import RulesScreen from './components/RulesScreen.jsx'
import ScoreBoard from './components/ScoreBoard.jsx'
import { useGame } from './game/useGame.js'
import { LANGUAGES, useLanguage } from './i18n/index.js'

function App() {
  const game = useGame()
  const { t, language, setLanguage } = useLanguage()

  // Keyboard shortcuts, same as the pygame version: 1-4, Enter, Space.
  useEffect(() => {
    if (game.screen !== 'playing') return

    function onKeyDown(event) {
      if (['1', '2', '3', '4'].includes(event.key)) {
        game.newQuestion(Number(event.key))
      } else if (event.key === 'Enter') {
        event.preventDefault() // don't also "click" a focused button
        game.check()
      } else if (event.key === ' ') {
        event.preventDefault() // don't scroll the page
        game.replay()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [game])

  return (
    <main className="app">
      <header className="header">
        <h1>{t.title}</h1>
        <div className="language-switch">
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
        </div>
      </header>

      {game.screen === 'rules' && <RulesScreen t={t} loading={game.loading} error={game.error} onStart={game.start} />}

      {game.screen === 'playing' && (
        <>
          <ScoreBoard t={t} points={game.points} mistakes={game.mistakes} />
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
                : game.result === 'wrong'
                  ? `${t.wrong(game.answer.join(' '))} ${t.next}`
                  : game.hasQuestion
                    ? t.hintListen
                    : t.hintChooseMode}
          </p>

          <Piano
            selected={game.selected}
            answer={game.answer}
            result={game.result}
            onPress={game.pressKey}
          />
        </>
      )}

      {(game.screen === 'won' || game.screen === 'lost') && (
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
