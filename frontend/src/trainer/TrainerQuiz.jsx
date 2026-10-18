import { spellNote } from '../game/keys.js'
import { INTERVALS, INVERSIONS, ROOTS, SEVENTHS, TEST_LENGTH, TRIADS, questionsAsked } from './trainerRules.js'

const ROOT_LABELS = ['C', 'C♯/D♭', 'D', 'D♯/E♭', 'E', 'F', 'F♯/G♭', 'G', 'G♯/A♭', 'A', 'A♯/B♭', 'B']

/** A row of answer buttons. After checking, the right one turns green and a wrong pick red. */
function AnswerButtons({ title, items, labels, value, correctValue, checked, onChoose }) {
  return (
    <div className="answer-group">
      {title && <h3>{title}</h3>}
      <div className="answer-buttons">
        {items.map((item) => {
          let className = 'button'
          if (checked && item === correctValue) className += ' button-correct'
          else if (checked && item === value) className += ' button-wrong'
          else if (item === value) className += ' button-active'
          return (
            <button key={String(item)} type="button" className={className} onClick={() => onChoose(item)}>
              {labels[item]}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function TrainerQuiz({ t, trainer }) {
  const { settings, question, given, checked, count, choose } = trainer
  const tt = t.trainer
  if (!question) return <section className="panel muted">…</section>

  const { answer } = question
  const asked = questionsAsked(answer, settings)
  const names = { ...tt.intervals, ...tt.triads, ...tt.sevenths }
  // Only the names the player chose to practice
  const nameItems = [
    ...INTERVALS.filter((i) => settings.intervals.includes(i)),
    ...TRIADS.filter((i) => settings.triads.includes(i)),
    ...SEVENTHS.filter((i) => settings.sevenths.includes(i)),
  ]
  const inversionItems = INVERSIONS.filter((i) => settings.inversions.includes(i) && (i < 3 || answer.name in tt.sevenths))
  const rootLabels = Object.fromEntries(ROOTS.map((root, i) => [root, ROOT_LABELS[i]]))

  const describe = () => {
    const parts = [names[answer.name]]
    if (answer.kind === 'chord') {
      parts.push(tt.inversions[answer.inversion])
      parts.push(`${tt.rootLabel} ${rootLabels[answer.root]}`)
    }
    return `${parts.join(' · ')}  (${question.notes.map((n) => spellNote(n, null)).join(' ')})`
  }

  return (
    <section className="panel trainer-quiz">
      <div className="quiz-header">
        <span>
          {settings.mode === 'test'
            ? tt.questionOf(Math.min(count.asked + (checked ? 0 : 1), TEST_LENGTH), TEST_LENGTH)
            : tt.practiceScore(count.correct, count.asked)}
        </span>
        <button type="button" className="link" onClick={trainer.backToSettings}>
          {tt.settingsButton}
        </button>
      </div>

      <button type="button" className="button replay-button" onClick={() => trainer.play()}>
        <kbd>Space</kbd> {t.replay}
      </button>

      <AnswerButtons
        title={tt.whatDidYouHear}
        items={nameItems}
        labels={names}
        value={given.name}
        correctValue={answer.name}
        checked={checked}
        onChoose={(name) => choose('name', name)}
      />
      {asked.inversion && (
        <AnswerButtons
          title={tt.voicingTitle}
          items={inversionItems}
          labels={tt.inversions}
          value={given.inversion}
          correctValue={answer.inversion}
          checked={checked}
          onChoose={(inversion) => choose('inversion', inversion)}
        />
      )}
      {asked.root && (
        <AnswerButtons
          title={tt.rootLabel}
          items={ROOTS}
          labels={rootLabels}
          value={given.root}
          correctValue={answer.root}
          checked={checked}
          onChoose={(root) => choose('root', root)}
        />
      )}

      {checked && (
        <p className={`message message-${checked.correct ? 'right' : 'wrong'}`} aria-live="polite">
          {checked.correct ? `${tt.right} ${describe()}` : tt.wrong(describe())}
        </p>
      )}

      <button
        type="button"
        className="button button-primary"
        onClick={checked ? trainer.next : trainer.check}
      >
        <kbd>Enter</kbd> {checked ? tt.next : t.check}
      </button>
    </section>
  )
}
