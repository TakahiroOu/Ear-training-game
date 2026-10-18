// One piano key. `status` sets its color (see keyStatus in game/rules.js).
export default function Key({ note, color, status, position, onPress }) {
  // Show the note name on C keys (to find your way) and on keys colored after checking.
  const isWhiteC = note.startsWith('C') && !note.includes('#')
  const showLabel = isWhiteC || ['correct', 'wrong', 'missed'].includes(status)

  return (
    <button
      type="button"
      className={`key key-${color} key-${status}`}
      style={position}
      aria-label={note}
      // pointerdown reacts the moment a finger/mouse touches the key (faster than click)
      onPointerDown={() => onPress(note)}
    >
      {showLabel && <span className="key-label">{note}</span>}
    </button>
  )
}
