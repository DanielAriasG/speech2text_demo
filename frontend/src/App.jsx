import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [file, setFile] = useState(null)
  const [model, setModel] = useState('whisper')
  const [segments, setSegments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamTranscription, setStreamTranscription] = useState([])
  const socketRef = useRef(null)
  const mediaRecorderRef = useRef(null)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleTranscribe = async () => {
    if (!file) {
      setError('Please select an audio file first.')
      return
    }

    setLoading(true)
    setError('')
    setSegments([])

    const formData = new FormData()
    formData.append('file', file)
    formData.append('model_name', model)

    try {
      const response = await fetch('http://localhost:8000/api/transcribe', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`)
      }

      const data = await response.json()
      setSegments(data.segments || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const startStreaming = async () => {
    setError('')
    setStreamTranscription([])
    setIsStreaming(true)

    socketRef.current = new WebSocket('ws://localhost:8000/api/ws/stream')

    socketRef.current.onopen = () => {
      console.log('WebSocket Connected')
    }

    socketRef.current.onmessage = (event) => {
      setStreamTranscription((prev) => [...prev, event.data])
    }

    socketRef.current.onerror = (err) => {
      setError('WebSocket Error')
      stopStreaming()
    }

    socketRef.current.onclose = () => {
      console.log('WebSocket Closed')
      setIsStreaming(false)
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorderRef.current = new MediaRecorder(stream)

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(event.data)
        }
      }

      mediaRecorderRef.current.start(1000) // Send chunk every second
    } catch (err) {
      setError('Could not access microphone.')
      stopStreaming()
    }
  }

  const stopStreaming = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
    }
    if (socketRef.current) {
      socketRef.current.close()
    }
    setIsStreaming(false)
  }

  const getSpeakerColor = (speaker) => {
    const colors = {
      'Speaker 1': '#4a90e2',
      'Speaker 2': '#e67e22',
      'Speaker 3': '#2ecc71',
      'Speaker 4': '#9b59b6',
      'Unknown': '#95a5a6'
    }
    return colors[speaker] || '#34495e'
  }

  return (
    <div className="App">
      <header>
        <h1>Modular ASR Platform</h1>
        <p>Professional Speech-to-Text & Diarization</p>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          File Upload
        </button>
        <button
          className={activeTab === 'stream' ? 'active' : ''}
          onClick={() => setActiveTab('stream')}
        >
          Live Streaming
        </button>
      </nav>

      <main className="content">
        {activeTab === 'upload' && (
          <section className="card">
            <div className="input-group">
              <label htmlFor="audio-file">Select Audio File</label>
              <input type="file" id="audio-file" accept="audio/*" onChange={handleFileChange} />
            </div>

            <div className="input-group">
              <label htmlFor="model-select">ASR Model</label>
              <select id="model-select" value={model} onChange={(e) => setModel(e.target.value)}>
                <option value="whisper">Whisper-large-v3</option>
                <option value="canary">NVIDIA Canary</option>
                <option value="parakeet">NVIDIA Parakeet</option>
              </select>
            </div>

            <button className="primary-btn" onClick={handleTranscribe} disabled={loading}>
              {loading ? 'Processing...' : 'Start Transcription'}
            </button>

            {error && <p className="error-msg">{error}</p>}

            {segments.length > 0 && (
              <div className="result-area">
                <h3>Transcription & Diarization</h3>
                <div className="segments-list">
                  {segments.map((s, idx) => (
                    <div key={idx} className="segment-item">
                      <span
                        className="speaker-badge"
                        style={{ backgroundColor: getSpeakerColor(s.speaker) }}
                      >
                        {s.speaker} [{s.start.toFixed(1)}s - {s.end.toFixed(1)}s]
                      </span>
                      <p className="segment-text">{s.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === 'stream' && (
          <section className="card">
            <div className="stream-controls">
              {!isStreaming ? (
                <button className="primary-btn start" onClick={startStreaming}>
                  Start Live Streaming
                </button>
              ) : (
                <button className="primary-btn stop" onClick={stopStreaming}>
                  Stop Streaming
                </button>
              )}
            </div>

            {error && <p className="error-msg">{error}</p>}

            <div className="result-area">
              <h3>Live Feed</h3>
              <div className="live-log">
                {streamTranscription.length === 0 && <p className="placeholder">No live data yet...</p>}
                {streamTranscription.map((msg, idx) => (
                  <p key={idx} className="log-entry">{msg}</p>
                ))}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
