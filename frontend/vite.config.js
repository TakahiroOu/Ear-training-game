import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Every HTML page of the site. index.html is the app; the others are pages for search engines
// (Japanese, with English versions under en/). New pages must be added here and to public/sitemap.xml.
const PAGES = [
  'index.html',
  'en/index.html',
  'choon-taisaku/index.html',
  'waon-kikiwake/index.html',
  'ontei-training/index.html',
  'en/dictation-exam-prep/index.html',
  'en/chord-ear-training/index.html',
  'en/interval-ear-training/index.html',
]

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: Object.fromEntries(PAGES.map((page) => [page.replace(/\/?index\.html$/, '') || 'app', resolve(page)])),
    },
  },
  server: {
    host: true, // listen on all addresses, needed inside Docker and for phones on your Wi-Fi
    port: 5173,
    // Send every request starting with /api to the Python backend.
    // Inside Docker the backend is called "backend"; outside Docker it's localhost.
    proxy: {
      '/api': {
        target: process.env.API_URL || 'http://localhost:8000',
        ws: true, // also forward WebSocket connections (live rooms)
      },
    },
    // Windows folders shared with Docker don't report file changes, so check for them regularly
    watch: { usePolling: true },
  },
})
