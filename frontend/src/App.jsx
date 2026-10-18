import { useEffect, useState } from 'react'

// Phase 0 page: proves the React frontend can talk to the Python backend.
// The real game (piano, sounds, scoring) replaces this in Phase 1.
function App() {
  const [backendStatus, setBackendStatus] = useState('checking...')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => response.json())
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('not reachable'))
  }, [])

  return (
    <main>
      <h1>Ear Training</h1>
      <p>
        Backend: <strong>{backendStatus}</strong>
      </p>
    </main>
  )
}

export default App
