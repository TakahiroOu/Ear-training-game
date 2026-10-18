// How contests are named on screen.

export function contestTitle(t, competition) {
  const category = t.contest.categories[competition.category]
  return competition.kind === 'ranked' ? t.contest.ranked(category) : `${competition.title} (${category})`
}

/** +150 / −50 */
export const signed = (points) => (points >= 0 ? `+${points}` : `−${Math.abs(points)}`)
