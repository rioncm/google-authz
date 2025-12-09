import { useCallback, useEffect, useState } from 'react'

export function useSession(baseUrl) {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${baseUrl}/session`, { credentials: 'include' })
      if (!res.ok) {
        throw new Error(`Session request failed (${res.status})`)
      }
      const payload = await res.json()
      setSession(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [baseUrl])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { session, refresh, loading, error }
}
