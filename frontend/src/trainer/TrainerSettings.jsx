import { NOTE_NAMES } from '../game/rules.js'
import { spellNote } from '../game/keys.js'
import { INTERVALS, INVERSIONS, NOTE_LENGTHS, SEVENTHS, TEST_LENGTH, TRIADS } from './trainerRules.js'

/** A group of checkboxes, with "All" / "None" shortcuts. */
function CheckboxGroup({ t, title, note, items, labels, selected, onChange }) {
  const toggle = (item) =>
    onChange(selected.includes(item) ? selected.filter((i) => i !== item) : items.filter((i) => i === item || selected.includes(i)))

  return (
    <fieldset className="settings-group">
      <legend>
        {title} <span className="muted">({selected.length})</span>
      </legend>
      <div className="quick-select">
        <button type="button" className="link" onClick={() => onChange(items)}>
          {t.selectAll}
        </button>
        <button type="button" className="link" onClick={() => onChange([])}>
          {t.selectNone}
        </button>
      </div>
      <div className="checkbox-grid">
        {items.map((item) => (
          <label key={item} className="checkbox">
            <input type="checkbox" checked={selected.includes(item)} onChange={() => toggle(item)} />
            {labels[item]}
          </label>
        ))}
      </div>
      {note && <p className="muted small">{note}</p>}
    </fieldset>
  )
}

/** Radio buttons shown as a row of buttons. */
function Choice({ options, value, onChange }) {
  return (
    <div className="choice">
      {options.map(([optionValue, label]) => (
        <button
          key={String(optionValue)}
          type="button"
          className={optionValue === value ? 'button button-active' : 'button'}
          onClick={() => onChange(optionValue)}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

export default function TrainerSettings({ t, trainer }) {
  const { settings, updateSettings, loading, error } = trainer
  const tt = t.trainer
  const noteOptions = (filter) =>
    NOTE_NAMES.filter(filter).map((note) => (
      <option key={note} value={note}>
        {spellNote(note, null)}
      </option>
    ))
  const indexOf = (note) => NOTE_NAMES.indexOf(note)

  return (
    <section className="panel trainer-settings">
      <h2>{tt.title}</h2>

      <CheckboxGroup
        t={tt}
        title={tt.intervalsTitle}
        items={INTERVALS}
        labels={tt.intervals}
        selected={settings.intervals}
        onChange={(intervals) => updateSettings({ intervals })}
      />
      <CheckboxGroup
        t={tt}
        title={tt.triadsTitle}
        items={TRIADS}
        labels={tt.triads}
        selected={settings.triads}
        onChange={(triads) => updateSettings({ triads })}
      />
      <CheckboxGroup
        t={tt}
        title={tt.seventhsTitle}
        items={SEVENTHS}
        labels={tt.sevenths}
        selected={settings.sevenths}
        onChange={(sevenths) => updateSettings({ sevenths })}
      />
      <CheckboxGroup
        t={tt}
        title={tt.voicingTitle}
        note={tt.voicingNote}
        items={INVERSIONS}
        labels={tt.inversions}
        selected={settings.inversions}
        onChange={(inversions) => updateSettings({ inversions: inversions.length ? inversions : [0] })}
      />

      <fieldset className="settings-group">
        <legend>{tt.rangeTitle}</legend>
        <div className="range">
          <select value={settings.low} onChange={(e) => updateSettings({ low: e.target.value })}>
            {noteOptions((note) => indexOf(note) < indexOf(settings.high))}
          </select>
          <span>➔</span>
          <select value={settings.high} onChange={(e) => updateSettings({ high: e.target.value })}>
            {noteOptions((note) => indexOf(note) > indexOf(settings.low))}
          </select>
        </div>
      </fieldset>

      <fieldset className="settings-group">
        <legend>{tt.playbackTitle}</legend>
        <Choice
          options={[
            ['harmonic', tt.harmonic],
            ['melodic', tt.melodic],
          ]}
          value={settings.playback}
          onChange={(playback) => updateSettings({ playback })}
        />
        <p className="muted small">{tt.alsoIdentify}</p>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={settings.askInversion}
            onChange={(e) => updateSettings({ askInversion: e.target.checked })}
          />
          {tt.askInversion}
        </label>
        <label className="checkbox">
          <input type="checkbox" checked={settings.askRoot} onChange={(e) => updateSettings({ askRoot: e.target.checked })} />
          {tt.askRoot}
        </label>
      </fieldset>

      <fieldset className="settings-group">
        <legend>{tt.noteLengthTitle}</legend>
        <Choice
          options={NOTE_LENGTHS.map((seconds) => [seconds, tt.seconds(seconds)])}
          value={settings.noteLength}
          onChange={(noteLength) => updateSettings({ noteLength })}
        />
      </fieldset>

      <fieldset className="settings-group">
        <legend>{tt.modeTitle}</legend>
        <Choice
          options={[
            ['practice', tt.practice],
            ['test', tt.test(TEST_LENGTH)],
          ]}
          value={settings.mode}
          onChange={(mode) => updateSettings({ mode })}
        />
      </fieldset>

      <button type="button" className="button button-primary start-button" disabled={loading} onClick={trainer.start}>
        {loading ? t.loadingSounds : tt.start}
      </button>
      {error && <p className="message message-error">{tt.errors[error]}</p>}
    </section>
  )
}
