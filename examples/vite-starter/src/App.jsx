import { useState } from 'react'
import { useSession } from './lib/useSession'
import { checkPermission } from './lib/authzClient'

const BASE_URL = __BASE_URL__
const REQUIRED_PERMISSION = __REQUIRED_PERMISSION__

export default function App() {
  const { session, refresh, loading, error } = useSession(BASE_URL)
  const [decision, setDecision] = useState(null)
  const [checkError, setCheckError] = useState(null)
  const [tokenType, setTokenType] = useState('session_token')
  const [tokenValue, setTokenValue] = useState('')

  const evaluatePermission = async () => {
    setCheckError(null)
    try {
      const result = await checkPermission(BASE_URL, REQUIRED_PERMISSION, tokenType, tokenValue)
      setDecision(result)
    } catch (err) {
      setCheckError(err.message)
    }
  }

  return (
    <main>
      <header>
        <h1>google-authz Vite starter</h1>
        <p>Base URL: {BASE_URL}</p>
      </header>
      <section>
        <button onClick={() => (window.location.href = `${BASE_URL}/login`)}>Sign in</button>
        <button onClick={refresh} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh session'}
        </button>
      </section>
      {error && <pre className="error">{error}</pre>}
      {session && (
        <section>
          <h2>EffectiveAuth snapshot</h2>
          <pre>{JSON.stringify(session, null, 2)}</pre>
        </section>
      )}
      <section>
        <h2>Permission check – {REQUIRED_PERMISSION}</h2>
        <label className="token-label">
          <span>Token type</span>
          <select value={tokenType} onChange={(event) => setTokenType(event.target.value)}>
            <option value="session_token">session_token</option>
            <option value="id_token">id_token</option>
          </select>
        </label>
        <textarea
          placeholder="Paste the token returned by google-authz or Google OAuth"
          value={tokenValue}
          onChange={(event) => setTokenValue(event.target.value)}
        />
        <button onClick={evaluatePermission}>Evaluate</button>
        {checkError && <pre className="error">{checkError}</pre>}
        {decision && (
          <pre>{JSON.stringify(decision, null, 2)}</pre>
        )}
      </section>
    </main>
  )
}
