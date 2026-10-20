import { useEffect, useState } from 'react'
import en from './en.js'
import ja from './ja.js'

export const LANGUAGES = { en, ja }

const STORAGE_KEY = 'language'

function initialLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved in LANGUAGES) return saved
  } catch {
    // storage can be blocked (e.g. private browsing): fall back to the browser language
  }
  return navigator.language.startsWith('ja') ? 'ja' : 'en'
}

/** Returns the texts for the current language (`t`) and a way to switch language. */
export function useLanguage() {
  const [language, setLanguageState] = useState(initialLanguage)

  // Tell the browser (and screen readers, translators, search engines) which language the page shows
  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  function setLanguage(next) {
    setLanguageState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // not saved, but the switch still works for this visit
    }
  }

  return { t: LANGUAGES[language], language, setLanguage }
}
