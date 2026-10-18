// How contests are named and timed on screen. Contest periods follow Japan time.

const TIME_ZONE = 'Asia/Tokyo'
const LOCALES = { en: 'en-US', ja: 'ja-JP' }

// The server sends UTC times without a time zone, so mark them as UTC
const toDate = (utcText) => new Date(utcText + 'Z')

export function contestTitle(t, competition, language) {
  const locale = LOCALES[language]
  const start = toDate(competition.starts_at)
  const day = start.toLocaleDateString(locale, { timeZone: TIME_ZONE, month: 'numeric', day: 'numeric' })
  switch (competition.kind) {
    case 'daily':
      return t.contest.daily(day)
    case 'weekly':
      return t.contest.weekly(day)
    case 'monthly':
      return t.contest.monthly(start.toLocaleDateString(locale, { timeZone: TIME_ZONE, year: 'numeric', month: 'long' }))
    default:
      return competition.title
  }
}

/** "ends in 5h 20m", or "ended" */
export function timeLeft(t, competition, now = Date.now()) {
  const ms = toDate(competition.ends_at) - now
  if (ms <= 0) return t.contest.ended
  const minutes = Math.floor(ms / 60000)
  return t.contest.endsIn(t.contest.duration(Math.floor(minutes / 1440), Math.floor(minutes / 60) % 24, minutes % 60))
}
