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

  return (
    <div className="App">
      <h1>Modular ASR Platform</h1>
      <div className="card">
        <div className="input-group">
          <label htmlFor="audio-file">Select Audio File:</label>
          <input type="file" id="audio-file" accept="audio/*" onChange={handleFileChange} />
        </div>

        <div className="input-group">
          <label htmlFor="model-select">Select ASR Model:</label>
          <select id="model-select" value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="whisper">Whisper</option>
            <option value="canary">Canary</option>
            <option value="parakeet">Parakeet</option>
          </select>
        </div>

        <button onClick={handleTranscribe} disabled={loading}>
          {loading ? 'Transcribing...' : 'Transcribe'}
        </button>

        {error && <p className="error">{error}</p>}

        {transcription && (
          <div className="result">
            <h2>Transcription:</h2>
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
      </div>
    </div>
  )
}

export default App
