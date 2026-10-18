import { MODES } from '../game/rules.js'

/** Buttons 1-4: play a new question with that many notes. */
export default function ModeSelector({ t, currentMode, onChoose }) {
  return (
    <div className="mode-selector">
      {MODES.map((mode) => (
        <button
          key={mode}
          type="button"
          className={mode === currentMode ? 'button button-active' : 'button'}
          onClick={() => onChoose(mode)}
        >
          <kbd>{mode}</kbd> {t.modeButton(mode)}
        </button>
      ))}
    </div>
  )
}
