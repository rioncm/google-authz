import { useEffect, useState } from 'react'

const BASE_URL = __BASE_URL__

export default function App() {
  const [session, setSession] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchSession = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${BASE_URL}/session`, { credentials: 'include' })
      if (!res.ok) {
        throw new Error(`Session request failed with ${res.status}`)
      }
      const data = await res.json()
      setSession(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSession()
  }, [])

  return (
    <main>
      <h1>google-authz React client</h1>
      <p>
        Use the button below to kick off the OAuth flow. Once the redirect finishes, refresh the session payload.
      </p>
      <div className="actions">
        <button onClick={() => (window.location.href = `${BASE_URL}/login`)}>Sign in with Google</button>
        <button onClick={fetchSession} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh /session'}
        </button>
      </div>
      {error && <pre className="error">{error}</pre>}
      {session && (
        <section className="payload">
          <h2>EffectiveAuth</h2>
          <pre>{JSON.stringify(session.effective_auth, null, 2)}</pre>
        </section>
      )}
    </main>
  )
}
