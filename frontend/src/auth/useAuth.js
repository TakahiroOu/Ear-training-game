import { useEffect, useState } from 'react'
import { supabase } from './supabase.js'

/** The logged-in user (or null) and the login actions. */
export function useAuth() {
  const [session, setSession] = useState(null)

  useEffect(() => {
    if (!supabase) return
    // Restore a login saved from an earlier visit, then follow log in / log out / token refresh
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data } = supabase.auth.onAuthStateChange((_event, newSession) => setSession(newSession))
    return () => data.subscription.unsubscribe()
  }, [])

  async function signUp(email, password) {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
    // With email confirmation on, there's no session until the user clicks the link in the email
    return { needsConfirmation: !data.session }
  }

  async function logIn(email, password) {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  async function logOut() {
    await supabase.auth.signOut()
  }

  return {
    enabled: supabase !== null,
    user: session?.user ?? null,
    token: session?.access_token ?? null, // sent to our backend to prove who you are
    signUp,
    logIn,
    logOut,
  }
}
