import { fetchMe } from '../api/client.js'
import { loadSounds } from '../audio/sampler.js'

/**
 * Before playing: start the sounds (browsers need a click for that) and check the player has a name.
 * Returns true when ready, false when the name form should be shown first.
 */
export async function readyToPlay(token) {
  await loadSounds()
  const me = await fetchMe(token)
  return Boolean(me.username)
}
