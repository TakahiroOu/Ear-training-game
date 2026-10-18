import { useEffect } from 'react'
import TrainerQuiz from './TrainerQuiz.jsx'
import TrainerSettings from './TrainerSettings.jsx'
import { useTrainer } from './useTrainer.js'

/** Interval & chord trainer: settings → questions → (test mode) summary. */
export default function TrainerPage({ t, auth }) {
  const trainer = useTrainer({ token: auth.token })
  const tt = t.trainer

  // Shortcuts: Space = replay, Enter = check / next question
  useEffect(() => {
    if (trainer.phase !== 'quiz') return
    function onKeyDown(event) {
      if (event.key === ' ') {
        event.preventDefault()
        trainer.play()
      } else if (event.key === 'Enter') {
        event.preventDefault()
        if (trainer.checked) trainer.next()
        else trainer.check()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [trainer])

  if (trainer.phase === 'settings') return <TrainerSettings t={t} trainer={trainer} />
  if (trainer.phase === 'quiz') return <TrainerQuiz t={t} trainer={trainer} />

  const { asked, correct } = trainer.count
  return (
    <section className="panel game-over">
      <h2>{tt.testDone}</h2>
      <p className="stat-value">{tt.testScore(correct, asked)}</p>
      <p className="muted">
        {!auth.token ? tt.loginToSave : trainer.saved === 'saved' ? tt.saved : trainer.saved === 'failed' ? t.saveFailed : ''}
      </p>
      <div className="actions">
        <button type="button" className="button button-primary" onClick={trainer.start}>
          {tt.tryAgain}
        </button>
        <button type="button" className="button" onClick={trainer.backToSettings}>
          {tt.settingsButton}
        </button>
      </div>
    </section>
  )
}
