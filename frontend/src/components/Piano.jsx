// The keyboard: 21 white + 15 black keys, C3 to B5 (replaces MakePiano.draw_piano).
import { BLACK_NOTES, WHITE_NOTES, keyStatus } from '../game/rules.js'
import Key from './Key.jsx'

// Sizes in % of the piano's width, so it stretches to fit the screen.
const WHITE_WIDTH = 100 / WHITE_NOTES.length
const BLACK_WIDTH = WHITE_WIDTH * 0.65

export default function Piano({ selected, answer, result, onPress }) {
  const round = { selected, answer, result }

  return (
    <div className="piano-scroll">
      <div className="piano">
        {WHITE_NOTES.map((note, i) => (
          <Key
            key={note}
            note={note}
            color="white"
            status={keyStatus(note, round)}
            position={{ left: `${i * WHITE_WIDTH}%`, width: `${WHITE_WIDTH}%` }}
            onPress={onPress}
          />
        ))}
        {BLACK_NOTES.map((note) => {
          // A black key sits on the line between its white key ("C#4" -> "C4") and the next one.
          const whiteIndex = WHITE_NOTES.indexOf(note.replace('#', ''))
          const left = (whiteIndex + 1) * WHITE_WIDTH - BLACK_WIDTH / 2
          return (
            <Key
              key={note}
              note={note}
              color="black"
              status={keyStatus(note, round)}
              position={{ left: `${left}%`, width: `${BLACK_WIDTH}%` }}
              onPress={onPress}
            />
          )
        })}
      </div>
    </div>
  )
}
