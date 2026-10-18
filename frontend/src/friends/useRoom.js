// A live room: one WebSocket connection that stays open, so the server can push
// questions and results to everyone at the same moment. Messages: see backend/app/routers/rooms.py.
import { useEffect, useRef, useState } from 'react'
import { roomSocketUrl } from '../api/client.js'
import { playNotes, playResult, prepareClip } from '../audio/sampler.js'

const FEED_LENGTH = 6

function base64ToArrayBuffer(text) {
  const bytes = Uint8Array.from(atob(text), (c) => c.charCodeAt(0))
  return bytes.buffer
}

export function useRoom(code, token) {
  const [room, setRoom] = useState(null) // players, scores, state, host, settings
  const [me, setMe] = useState(null) // my player id
  const [question, setQuestion] = useState(null) // { round, mode, seconds, receivedAt }
  const [selected, setSelected] = useState([])
  const [reveal, setReveal] = useState(null) // { round, notes, scorers }
  const [standings, setStandings] = useState(null)
  const [feed, setFeed] = useState([]) // latest events: { kind, player, points, rank }
  const [error, setError] = useState(null)
  const socket = useRef(null)
  const clip = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(roomSocketUrl(code))
    socket.current = ws
    ws.onopen = () => ws.send(JSON.stringify({ type: 'auth', token }))
    ws.onclose = () => setError((current) => current ?? 'disconnected')
    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data)
      switch (message.type) {
        case 'welcome':
          setMe(message.you)
          break
        case 'room':
          setRoom(message)
          if (message.state !== 'finished') setStandings(null)
          break
        case 'question': {
          setSelected([])
          setReveal(null)
          setFeed([])
          setQuestion({ ...message, audio: undefined, receivedAt: Date.now() })
          clip.current?.dispose()
          clip.current = await prepareClip(base64ToArrayBuffer(message.audio))
          clip.current.play()
          break
        }
        case 'correct':
        case 'wrong':
          setFeed((current) => [{ kind: message.type, ...message }, ...current].slice(0, FEED_LENGTH))
          break
        case 'reveal':
          setReveal(message)
          break
        case 'finished':
          setStandings(message.standings)
          break
        case 'error':
          setError(message.error)
          break
      }
    }
    return () => {
      ws.close()
      clip.current?.dispose()
    }
  }, [code, token])

  const send = (message) => socket.current?.readyState === WebSocket.OPEN && socket.current.send(JSON.stringify(message))
  const answeredAlready = Boolean(room?.answered.includes(me))
  const canAnswer = room?.state === 'question' && question && !answeredAlready

  function pressKey(note) {
    playNotes([note])
    if (!canAnswer) return
    setSelected((current) => (current.includes(note) ? current.filter((n) => n !== note) : [...current, note]))
  }

  function submit() {
    if (!canAnswer || selected.length === 0) return
    send({ type: 'answer', round: question.round, notes: selected })
  }

  // Play the right/wrong sound when the server tells us how our answer went
  const latest = feed[0]
  const lastSound = useRef(null)
  useEffect(() => {
    if (latest && latest.player === me && lastSound.current !== latest) {
      lastSound.current = latest
      playResult(latest.kind === 'correct')
    }
  }, [latest, me])

  return {
    room, me, question, selected, reveal, standings, feed, error, canAnswer, answeredAlready,
    isHost: room?.host === me,
    pressKey,
    submit,
    replay: () => clip.current?.play(),
    configure: (category, target) => send({ type: 'configure', category, target }),
    start: () => send({ type: 'start' }),
    end: () => send({ type: 'end' }),
    clearError: () => setError(null),
  }
}
