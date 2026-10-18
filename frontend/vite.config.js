import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // listen on all addresses, needed inside Docker and for phones on your Wi-Fi
    port: 5173,
    // Send every request starting with /api to the Python backend.
    // Inside Docker the backend is called "backend"; outside Docker it's localhost.
    proxy: {
      '/api': process.env.API_URL || 'http://localhost:8000',
    },
    // Windows folders shared with Docker don't report file changes, so check for them regularly
    watch: { usePolling: true },
  },
})
