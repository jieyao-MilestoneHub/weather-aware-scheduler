import { useState } from 'react'
import './index.css'

function App() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSchedule = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/schedule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input }),
      })

      const data = await response.json()

      if (data.status === 'success') {
        setResult(data.result)
      } else {
        setError(data.error || 'An unknown error occurred')
      }
    } catch (err) {
      setError('Failed to connect to the server. Please ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Weather Scheduler</h1>

      <div className="card">
        <form onSubmit={handleSchedule}>
          <div className="input-group">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g., Tomorrow 2pm Taipei meet Alice 60min"
              disabled={loading}
            />
          </div>
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? <div className="loading-spinner" /> : 'Schedule Meeting'}
          </button>
        </form>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {result && (
          <div className="event-details">
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <span className="status-badge">
                {result.status === 'confirmed' ? '✓ Scheduled' : result.status}
              </span>
            </div>

            <div className="event-row">
              <span className="label">City</span>
              <span className="value">{result.city}</span>
            </div>

            <div className="event-row">
              <span className="label">Time</span>
              <span className="value">
                {new Date(result.datetime_iso).toLocaleString()}
              </span>
            </div>

            <div className="event-row">
              <span className="label">Duration</span>
              <span className="value">{result.duration_min} mins</span>
            </div>

            <div className="event-row">
              <span className="label">Attendees</span>
              <span className="value">{result.attendees.join(', ')}</span>
            </div>

            {result.notes && (
              <div className="event-row">
                <span className="label">Notes</span>
                <span className="value">{result.notes}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
