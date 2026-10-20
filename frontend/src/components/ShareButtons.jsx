import { useState } from 'react'

// The public address of the site (see frontend/.env.production)
const SITE_URL = `${import.meta.env.VITE_SITE_URL || window.location.origin}/`

/** "Share your result": the phone's share menu (if any), X, LINE and copy. Every share is a new link to the site. */
export default function ShareButtons({ t, text }) {
  const [copied, setCopied] = useState(false)
  const full = `${text} ${SITE_URL}`

  async function shareWithPhone() {
    try {
      await navigator.share({ text, url: SITE_URL })
    } catch {
      // the person closed the share menu: nothing to do
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(full)
      setCopied(true)
    } catch {
      window.prompt(t.share.copyManually, full) // clipboard blocked: let them copy it by hand
    }
  }

  return (
    <div className="share">
      <span className="muted small">{t.share.title}</span>
      <div className="share-buttons">
        {typeof navigator.share === 'function' && (
          <button type="button" className="button" onClick={shareWithPhone}>
            {t.share.share}
          </button>
        )}
        <a
          className="button"
          href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(SITE_URL)}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          X
        </a>
        <a
          className="button"
          href={`https://line.me/R/share?text=${encodeURIComponent(full)}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          LINE
        </a>
        <button type="button" className="button" onClick={copy}>
          {copied ? t.share.copied : t.share.copy}
        </button>
      </div>
    </div>
  )
}
