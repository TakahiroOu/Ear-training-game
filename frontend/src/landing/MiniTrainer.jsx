import { useState } from 'react'
import { loadSounds, playMelody, playNotes, playResult } from '../audio/sampler.js'
import { CHOICES, QUESTION_MAKERS } from './miniQuestions.js'
import TEXTS from './texts.js'

/** play the question: intervals one by one then together, degrees after the reference C */
function play(question) {
  if (question.kind === 'interval') {
    playMelody(question.notes, 0.8)
    setTimeout(() => playNotes(question.notes, 1.5), 1800)
  } else if (question.kind === 'degree') {
    playMelody([question.reference, question.notes[0]], 0.9)
  } else {
    playNotes(question.notes, 2)
  }
}

/** A small trainer for the guide pages: listen, pick a name, see if it was right. */
export default function MiniTrainer({ kind, lang }) {
  const t = TEXTS[lang]
  const [status, setStatus] = useState('idle') // idle | loading | asking | answered
  const [question, setQuestion] = useState(null)
  const [picked, setPicked] = useState(null)
  const [score, setScore] = useState({ right: 0, asked: 0 })

  async function next() {
    if (status === 'idle') {
      setStatus('loading')
      await loadSounds() // the first click lets the browser play sound
    }
    const fresh = QUESTION_MAKERS[kind]()
    setQuestion(fresh)
    setPicked(null)
    setStatus('asking')
    play(fresh)
  }

  function answer(choice) {
    if (status !== 'asking') return
    const right = choice === question.answer
    playResult(right)
    setPicked(choice)
    setScore((s) => ({ right: s.right + (right ? 1 : 0), asked: s.asked + 1 }))
    setStatus('answered')
  }

  return (
    <div className="mini-trainer">
      <p className="mini-instruction">{t.instructions[kind]}</p>
      <div className="mini-controls">
        <button type="button" className="button button-primary" disabled={status === 'loading'} onClick={next}>
          {status === 'loading' ? t.loading : status === 'idle' ? t.start : status === 'asking' ? t.newQuestion : t.next}
        </button>
        {question && (
          <button type="button" className="button" onClick={() => play(question)}>
            {t.replay}
          </button>
        )}
        {score.asked > 0 && <span className="mini-score">{t.score(score.right, score.asked)}</span>}
      </div>
      {question && (
        <div className="answer-buttons">
          {CHOICES[kind].map((choice) => {
            let className = 'button'
            if (status === 'answered' && choice === question.answer) className += ' button-correct'
            else if (status === 'answered' && choice === picked) className += ' button-wrong'
            return (
              <button key={choice} type="button" className={className} onClick={() => answer(choice)}>
                {t.names[kind][choice]}
              </button>
            )
          })}
        </div>
      )}
      {status === 'answered' && (
        <p className={picked === question.answer ? 'message message-right' : 'message message-wrong'}>
          {picked === question.answer ? t.right : t.wrong(t.names[kind][question.answer])}
        </p>
      )}
      <p>
        <a className="button button-primary mini-cta" href={lang === 'en' ? '/?lang=en' : '/'}>
          {t.openApp}
        </a>
      </p>
    </div>
  )
}
