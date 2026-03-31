import { useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [model, setModel] = useState('whisper')
  const [diarizationModel, setDiarizationModel] = useState('pyannote')
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
    formData.append('diarization_model', diarizationModel)

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

  const getSpeakerClass = (speaker) => {
    if (!speaker) return ''
    const num = speaker.replace(/\D/g, '')
    return `speaker-${num % 4}`
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

        <div className="input-group">
          <label htmlFor="diar-model-select">Diarization Model:</label>
          <select id="diar-model-select" value={diarizationModel} onChange={(e) => setDiarizationModel(e.target.value)}>
            <option value="pyannote">Pyannote</option>
            <option value="sortformer">Sortformer 4-Speaker</option>
          </select>
        </div>

        <button onClick={handleTranscribe} disabled={loading}>
          {loading ? 'Transcribing...' : 'Transcribe'}
        </button>

        {error && <p className="error" role="alert">{error}</p>}

        {transcription && (
          <div className="result" aria-live="polite">
            <h2>Transcription Results:</h2>

            {diarization && diarization.length > 0 ? (
              <div className="diarization-view">
                {diarization.map((segment, idx) => (
                  <div key={idx} className={`segment ${getSpeakerClass(segment.speaker)}`}>
                    <div className="segment-info">
                      <span className="speaker-name">{segment.speaker}</span>
                      <span className="timestamp">{segment.start.toFixed(2)}s - {segment.end.toFixed(2)}s</span>
                    </div>
                    <p className="segment-text">{segment.text}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p>{transcription}</p>
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
