// Supabase is used ONLY for logging in (see docs/PLAN.md, "Safety rule").
// Game data always goes through our own backend (api/client.js).
import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// null until the keys are filled in .env, and then the app simply works without accounts
export const supabase = url && anonKey ? createClient(url, anonKey) : null
