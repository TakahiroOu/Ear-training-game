import { MODES } from '../game/rules.js'

/**
 * "How many notes" buttons 1-4: play a new question with that many notes.
 * Locked while a question is waiting for an answer, so a question can't be skipped.
 */
export default function ModeSelector({ t, currentMode, locked, onChoose }) {
  return (
    <div className="mode-selector-group">
      <span className="mode-label">{t.modeLabel}</span>
      <div className="mode-selector">
        {MODES.map((mode) => (
          <button
            key={mode}
            type="button"
            className={mode === currentMode ? 'button button-active' : 'button'}
            disabled={locked}
            onClick={() => onChoose(mode)}
          >
            <kbd>{mode}</kbd> {t.modeButton(mode)}
          </button>
        ))}
      </div>
    </div>
  )
}
