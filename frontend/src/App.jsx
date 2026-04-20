import { useState, useRef, useEffect } from 'react'
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

  // Streaming specific state
  const [isStreaming, setIsStreaming] = useState(false)
  const [liveTranscription, setLiveTranscription] = useState('')
  const mediaRecorderRef = useRef(null)
  const socketRef = useRef(null)
  const accumulatedChunksRef = useRef([])

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

  const handleDownload = (format, base64Data) => {
    if (base64Data) {
      let mimeType = 'text/plain';
      if (format === 'docx') mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      if (format === 'pdf') mimeType = 'application/pdf';

      // Convert base64 to binary ArrayBuffer
      const binaryString = window.atob(base64Data);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const blob = new Blob([bytes], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `transcription.${format}`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const startStreaming = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      setError('')
      setLiveTranscription('')
      accumulatedChunksRef.current = []

      socketRef.current = new WebSocket('ws://localhost:8000/api/ws/stream')

      socketRef.current.onmessage = (event) => {
        setLiveTranscription(event.data)
      }

      socketRef.current.onerror = (e) => {
        console.error('WebSocket Error', e)
        setError('Streaming connection error.')
      }

      // Record in chunks
      mediaRecorderRef.current = new MediaRecorder(stream)
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current.readyState === WebSocket.OPEN) {
          // Accumulate blobs so the backend gets a valid playable file of increasing length
          accumulatedChunksRef.current.push(event.data)
          const aggregateBlob = new Blob(accumulatedChunksRef.current, { type: mediaRecorderRef.current.mimeType })
          socketRef.current.send(aggregateBlob)
        }
      }

      // Fire a chunk every 2 seconds
      mediaRecorderRef.current.start(2000)
      setIsStreaming(true)
    } catch (err) {
      setError('Could not access microphone: ' + err.message)
    }
  }

  const stopStreaming = () => {
    if (mediaRecorderRef.current && isStreaming) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsStreaming(false)
    }
    if (socketRef.current) {
      socketRef.current.close()
    }
  }

  return (
    <div className="App">
      <h1>Modular ASR Platform</h1>
      <div className="card">
        <div className="streaming-section" style={{ borderBottom: '1px solid #ccc', paddingBottom: '1rem' }}>
          <h2>Live Dictation (Streaming)</h2>
          {!isStreaming ? (
            <button onClick={startStreaming} style={{ backgroundColor: '#4CAF50' }}>Start Mic Streaming</button>
          ) : (
            <button onClick={stopStreaming} style={{ backgroundColor: '#F44336' }}>Stop Streaming</button>
          )}
          {liveTranscription && (
            <div className="result" style={{ marginTop: '1rem', backgroundColor: '#e3f2fd' }}>
              <p>{liveTranscription}</p>
            </div>
          )}
        </div>

        <div className="upload-section">
          <h2>Offline Multi-Speaker Translation</h2>
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
            <label htmlFor="diarization-select">Select Diarization Model:</label>
            <select id="diarization-select" value={diarizationModel} onChange={(e) => setDiarizationModel(e.target.value)}>
              <option value="pyannote">Pyannote 3.1</option>
              <option value="sortformer">NeMo Sortformer</option>
              <option value="diarizen">DiariZen Meeting Base</option>
            </select>
          </div>

          <button onClick={handleTranscribe} disabled={loading}>
            {loading ? 'Transcribing...' : 'Transcribe File'}
          </button>
        </div>

        {error && <p className="error">{error}</p>}

        {diarization && diarization.length > 0 && (
          <div className="result">
            <h2>Transcription with Speakers:</h2>
            <div className="diarization-blocks">
              {diarization.map((segment, idx) => {
                const speakerNum = parseInt(segment.speaker.replace(/[^0-9]/g, '')) || 0;
                const colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#F44336', '#00BCD4'];
                const color = colors[speakerNum % colors.length];

                return (
                  <div key={idx} className="speaker-segment">
                    <span
                      className="speaker-badge"
                      style={{ backgroundColor: color }}
                    >
                      {segment.speaker} ({segment.start}s - {segment.end}s)
                    </span>
                    <p>{segment.text}</p>
                  </div>
                );
              })}
            </div>

            {exports && (
              <div className="exports" style={{ display: 'flex', gap: '10px', marginTop: '1rem' }}>
                <button onClick={() => handleDownload('txt', exports.txt)}>Download TXT</button>
                {exports.docx && <button onClick={() => handleDownload('docx', exports.docx)}>Download DOCX</button>}
                {exports.pdf && <button onClick={() => handleDownload('pdf', exports.pdf)}>Download PDF</button>}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App