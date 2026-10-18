// How contests are named and timed on screen.

const toDate = (utcText) => new Date(utcText + 'Z') // the server sends UTC times without a time zone

export function contestTitle(t, competition) {
  const category = t.contest.categories[competition.category]
  return competition.kind === 'ranked' ? t.contest.ranked(category) : `${competition.title} (${category})`
}

/** "ends in 5h 20m", or "ended" (class competitions only; ranked ones never end) */
export function timeLeft(t, competition, now = Date.now()) {
  const ms = toDate(competition.ends_at) - now
  if (ms <= 0) return t.contest.ended
  const minutes = Math.floor(ms / 60000)
  return t.contest.endsIn(t.contest.duration(Math.floor(minutes / 1440), Math.floor(minutes / 60) % 24, minutes % 60))
}

/** +150 / −50 */
export const signed = (points) => (points >= 0 ? `+${points}` : `−${Math.abs(points)}`)
