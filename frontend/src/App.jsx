import { useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [model, setModel] = useState('whisper')
  const [transcription, setTranscription] = useState('')
  const [diarization, setDiarization] = useState([])
  const [exports, setExports] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copySuccess, setCopySuccess] = useState(false)

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
    setTranscription('')
    setDiarization([])
    setExports(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('model_name', model)

    try {
      const response = await fetch('http://localhost:8000/api/transcribe', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Error: ${response.statusText}`)
      }

      const data = await response.json()
      setTranscription(data.transcription)
      setDiarization(data.diarization)
      setExports(data.exports)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (exports && exports.txt) {
      const blob = new Blob([atob(exports.txt)], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'transcription.txt'
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(transcription)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy!', err)
    }
  }

  return (
    <div className="App">
      <h1>Modular ASR Platform</h1>
      <main className="card">
        <div className="input-group">
          <label htmlFor="audio-file">Select Audio File:</label>
          <input
            type="file"
            id="audio-file"
            accept="audio/*"
            onChange={handleFileChange}
          />
        </div>

        <div className="input-group">
          <label htmlFor="model-select">Select ASR Model:</label>
          <select
            id="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            <option value="whisper">Whisper</option>
            <option value="canary">Canary</option>
            <option value="parakeet">Parakeet</option>
          </select>
        </div>

        <button onClick={handleTranscribe} disabled={loading} aria-busy={loading}>
          {loading ? 'Transcribing...' : 'Transcribe'}
        </button>

        {error && (
          <p className="error" role="alert" aria-live="assertive">
            {error}
          </p>
        )}

        {transcription && (
          <div className="result" aria-live="polite">
            <div className="result-header">
              <h2>Transcription:</h2>
              <button
                className="copy-btn"
                onClick={handleCopy}
                aria-label="Copy transcription to clipboard"
                title={copySuccess ? 'Copied!' : 'Copy to clipboard'}
              >
                {copySuccess ? (
                  <svg
                    viewBox="0 0 24 24"
                    width="18"
                    height="18"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                ) : (
                  <svg
                    viewBox="0 0 24 24"
                    width="18"
                    height="18"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                  </svg>
                )}
              </button>
            </div>
            <p>{transcription}</p>

            {diarization && diarization.length > 0 && (
              <div className="diarization">
                <h3>Speaker Diarization:</h3>
                <ul>
                  {diarization.map((segment, idx) => (
                    <li key={idx}>
                      <strong>{segment.speaker}:</strong> {segment.start}s - {segment.end}s
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {exports && (
              <div className="exports">
                <button onClick={handleDownload}>Download TXT</button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
