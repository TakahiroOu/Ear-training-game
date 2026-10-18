import { KEYS } from '../game/keys.js'

/** Choose a key (調性): questions then use only its notes and chords. */
export default function KeySelector({ t, language, value, onChange, onHearKey }) {
  const options = (quality) =>
    KEYS.filter((key) => key.id.endsWith(quality)).map((key) => (
      <option key={key.id} value={key.id}>
        {key[language]}
      </option>
    ))

  return (
    <div className="key-selector">
      <label>
        {t.keyLabel}
        <select
          value={value ?? ''}
          onChange={(event) => {
            onChange(event.target.value || null)
            event.currentTarget.blur() // so the 1-4 / Enter / Space shortcuts go to the game again
          }}
        >
          <option value="">{t.noKey}</option>
          <optgroup label={t.majorKeys}>{options('major')}</optgroup>
          <optgroup label={t.minorKeys}>{options('minor')}</optgroup>
        </select>
      </label>
      <button type="button" className="button" disabled={!value} onClick={onHearKey}>
        <kbd>K</kbd> {t.hearKey}
      </button>
    </div>
  )
}
