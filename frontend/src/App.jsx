import React, { useState, useRef, useEffect } from 'react';

export default function App() {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('whisper');
  const [diarizationModel, setDiarizationModel] = useState('sortformer');
  const [language, setLanguage] = useState('');
  const [transcription, setTranscription] = useState('');
  const [diarization, setDiarization] = useState([]);
  const [exports, setExports] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Streaming specific state
  const [isStreaming, setIsStreaming] = useState(false);
  const [liveTranscription, setLiveTranscription] = useState('');
  const mediaRecorderRef = useRef(null);
  const socketRef = useRef(null);
  const accumulatedChunksRef = useRef([]);
  const fileInputRef = useRef(null);

  const europeanLanguages = [
    { code: '', label: 'Auto-Detect' },
    { code: 'en', label: 'English' },
    { code: 'es', label: 'Spanish' },
    { code: 'pl', label: 'Polish' },
    { code: 'fr', label: 'French' },
    { code: 'de', label: 'German' },
    { code: 'it', label: 'Italian' },
    { code: 'pt', label: 'Portuguese' },
    { code: 'nl', label: 'Dutch' },
    { code: 'ru', label: 'Russian' },
    { code: 'tr', label: 'Turkish' },
    { code: 'el', label: 'Greek' }
  ];

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleTranscribe = async () => {
    if (!file) {
      setError('Please select an audio file first.');
      return;
    }

    setLoading(true);
    setError('');
    setTranscription('');
    setDiarization([]);
    setExports(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_name', model);
    formData.append('diarization_model', diarizationModel);

    if (language) {
      formData.append('language', language);
    }

    try {
      const response = await fetch('http://localhost:8000/api/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Error: ${response.statusText}`);
      }

      const data = await response.json();
      setTranscription(data.transcription);
      setDiarization(data.diarization);
      setExports(data.exports);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format, base64Data) => {
    if (base64Data) {
      let mimeType = 'text/plain';
      if (format === 'docx') mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      if (format === 'pdf') mimeType = 'application/pdf';

      const binaryString = window.atob(base64Data);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const blob = new Blob([bytes], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transcription.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const startStreaming = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setError('');
      setLiveTranscription('');
      accumulatedChunksRef.current = [];

      socketRef.current = new WebSocket('ws://localhost:8000/api/ws/stream');

      socketRef.current.onmessage = (event) => {
        setLiveTranscription(event.data);
      };

      socketRef.current.onerror = (e) => {
        console.error('WebSocket Error', e);
        setError('Streaming connection error.');
      };

      mediaRecorderRef.current = new MediaRecorder(stream);
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current.readyState === WebSocket.OPEN) {
          accumulatedChunksRef.current.push(event.data);
          const aggregateBlob = new Blob(accumulatedChunksRef.current, { type: mediaRecorderRef.current.mimeType });
          socketRef.current.send(aggregateBlob);
        }
      };

      mediaRecorderRef.current.start(2000);
      setIsStreaming(true);
    } catch (err) {
      setError('Could not access microphone: ' + err.message);
    }
  };

  const stopStreaming = () => {
    if (mediaRecorderRef.current && isStreaming) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsStreaming(false);
    }
    if (socketRef.current) {
      socketRef.current.close();
    }
  };

  // Sort and process speakers
  const sortedDiarization = [...diarization].sort((a, b) => a.start - b.start);
  const speakerMap = {};
  let speakerCounter = 0;
  sortedDiarization.forEach(segment => {
    if (speakerMap[segment.speaker] === undefined) {
      speakerMap[segment.speaker] = speakerCounter++;
    }
  });

  const speakerStyles = [
    { bg: 'bg-secondary-green', text: 'text-black' }, // S0
    { bg: 'bg-secondary-pink', text: 'text-black' },  // S1
    { bg: 'bg-primary-coral', text: 'text-white' },   // S2
    { bg: 'bg-secondary-grey', text: 'text-black' },  // S3
    { bg: 'bg-primary-green', text: 'text-white' }    // S4
  ];

  return (
    <div className="app-container min-h-screen py-12 px-4">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        :root {
          --primary-green: #026873;
          --primary-coral: #ED6D7C;
          --secondary-green: #41B9C6;
          --secondary-pink: #F1A6A0;
          --secondary-grey: #C1D0D9;
        }

        .app-container {
          background-color: #f8fafc;
          font-family: 'Inter', sans-serif;
        }

        /* Brand Text Colors */
        .text-primary-green { color: var(--primary-green); }
        .text-primary-coral { color: var(--primary-coral); }
        .text-secondary-grey { color: var(--secondary-grey); }

        /* Brand Background Colors */
        .bg-primary-green { background-color: var(--primary-green); }
        .bg-primary-coral { background-color: var(--primary-coral); }
        .bg-secondary-green { background-color: var(--secondary-green); }
        .bg-secondary-pink { background-color: var(--secondary-pink); }
        .bg-secondary-grey { background-color: var(--secondary-grey); }

        /* Brand Border Colors */
        .border-secondary-grey { border-color: var(--secondary-grey); }

        /* Custom Component States */
        .dropzone-active { background-color: rgba(65, 185, 198, 0.05); }
        .dropzone-inactive { background-color: #fafafa; }

        .focus-ring-primary:focus {
          outline: none;
          --tw-ring-color: var(--primary-green);
          box-shadow: 0 0 0 2px var(--tw-ring-color);
        }

        .soft-card-shadow {
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        }

        /* Custom scrollbar for transcription viewer */
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1; 
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: var(--secondary-grey); 
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: var(--primary-green); 
        }
      `}</style>

      {/* Page Header */}
      <header className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold mb-3 tracking-tight text-primary-green">
          eCAN + ASR
        </h1>
      </header>

      {/* Main Dashboard Container */}
      <main className="max-w-6xl mx-auto bg-white rounded-xl soft-card-shadow border border-gray-100 overflow-hidden">
        <div className="flex flex-col lg:flex-row">

          {/* Left Panel: Controls */}
          <section className="lg:w-1/2 p-8 border-r border-gray-100 flex flex-col">

            {/* Live Dictation Section */}
            <div className="mb-10">
              <h2 className="text-lg font-semibold mb-6 text-primary-green">Live Dictation (Streaming)</h2>
              <div className="flex items-center gap-6">
                {!isStreaming ? (
                  <button
                    onClick={startStreaming}
                    className="flex items-center gap-3 px-6 py-4 rounded-full shadow-sm hover:shadow-md transition-shadow duration-200 text-white font-medium bg-primary-green"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                    </svg>
                    <span>Start Recording</span>
                  </button>
                ) : (
                  <button
                    onClick={stopStreaming}
                    className="flex items-center gap-3 px-6 py-4 rounded-full shadow-sm hover:shadow-md transition-shadow duration-200 text-white font-medium animate-pulse bg-primary-coral"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>
                    </svg>
                    <span>Stop Recording</span>
                  </button>
                )}

                {/* Visualizer Placeholder */}
                <div className="flex-grow h-12 flex items-center justify-center opacity-50">
                  {isStreaming ? (
                    <div className="flex items-end gap-1 h-full">
                      {[...Array(12)].map((_, i) => (
                        <div key={i} className="w-1.5 rounded-t-sm animate-pulse bg-primary-green" style={{ height: `${Math.random() * 100}%`, animationDelay: `${i * 0.1}s` }}></div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-sm italic text-secondary-grey">Microphone inactive</span>
                  )}
                </div>
              </div>

              {liveTranscription && (
                <div className="mt-6 p-4 rounded-lg bg-gray-50 border border-gray-100 text-sm text-gray-700 italic">
                  "{liveTranscription}"
                </div>
              )}
            </div>

            <hr className="mb-10 border-gray-100" />

            {/* Offline Multi-Speaker Section */}
            <div className="flex-grow">
              <h2 className="text-lg font-semibold mb-6 text-primary-green">Offline Multi-Speaker Translation</h2>

              {/* Drag and Drop Area */}
              <div
                className={`border-2 border-dashed rounded-xl p-8 mb-6 text-center transition-colors cursor-pointer border-secondary-grey ${file ? 'dropzone-active' : 'dropzone-inactive'}`}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  accept="audio/*"
                  onChange={handleFileChange}
                />
                {file ? (
                  <p className="text-gray-800 font-medium break-all">
                    Selected: <span className="text-primary-green">{file.name}</span>
                  </p>
                ) : (
                  <>
                    <p className="text-gray-600">
                      <span className="font-bold text-gray-800">Drag & Drop</span> or <span className="font-medium text-primary-green">Click to Select Audio File</span>
                    </p>
                    <p className="text-xs text-gray-400 mt-1">(MP3/WAV supported)</p>
                  </>
                )}
              </div>

              {/* Settings Configuration */}
              <div className="space-y-4 mb-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">ASR Model</label>
                    <select
                      className="w-full rounded-lg border border-gray-300 bg-white text-sm py-3 px-3 shadow-sm focus-ring-primary"
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      disabled={loading}
                    >
                      <option value="whisper">Whisper (OpenAI)</option>
                      <option value="canary">Canary (NVIDIA)</option>
                      <option value="parakeet">Parakeet (NVIDIA)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Diarization</label>
                    <select
                      className="w-full rounded-lg border border-gray-300 bg-white text-sm py-3 px-3 shadow-sm focus-ring-primary"
                      value={diarizationModel}
                      onChange={(e) => setDiarizationModel(e.target.value)}
                      disabled={loading}
                    >
                      <option value="sortformer">NeMo Sortformer</option>
                      <option value="pyannote">Pyannote Audio 3.1</option>
                      <option value="diarizen">DiariZen Meeting</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Target Language</label>
                  <select
                    className="w-full rounded-lg border border-gray-300 bg-white text-sm py-3 px-3 shadow-sm focus-ring-primary"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    disabled={loading}
                  >
                    {europeanLanguages.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {error && <p className="text-sm font-medium mb-4 text-primary-coral">{error}</p>}

              {/* Transcribe Button */}
              <button
                className="w-full text-white font-medium py-3 rounded-lg shadow-md transition-colors duration-200 mb-6 flex justify-center items-center disabled:opacity-50 disabled:cursor-not-allowed bg-primary-green"
                onClick={handleTranscribe}
                disabled={loading || !file}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing Audio...
                  </>
                ) : 'Transcribe File'}
              </button>

              {loading && (
                <div className="space-y-2">
                  <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                    <div className="h-1.5 rounded-full animate-pulse w-full bg-secondary-green"></div>
                  </div>
                  <p className="text-xs text-gray-500 font-medium text-center">Analyzing inference models...</p>
                </div>
              )}
            </div>

            {/* EU Branding Footer */}
            <div className="mt-8 pt-6 border-t border-gray-100 flex items-start gap-4">
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/b/b7/Flag_of_Europe.svg"
                alt="European Union Emblem"
                className="w-12 h-auto rounded-sm flex-shrink-0"
              />
              <p className="text-[10px] leading-tight text-gray-500">
                Co-funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European Health and Digital Executive Agency (HaDEA). Neither the European Union nor the granting authority can be held responsible for them.
              </p>
            </div>

          </section>

          {/* Right Panel: Viewer */}
          <section className="lg:w-1/2 p-8 bg-gray-50 flex flex-col h-[800px] lg:h-auto relative">

            {/* Header Actions */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 pb-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold mb-4 sm:mb-0 text-primary-green">Transcription Results</h2>

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleDownload('txt', exports?.txt)}
                  disabled={!exports?.txt}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-md text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                  TXT
                </button>
                <button
                  onClick={() => handleDownload('docx', exports?.docx)}
                  disabled={!exports?.docx}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-md text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                  DOCX
                </button>
                <button
                  onClick={() => handleDownload('pdf', exports?.pdf)}
                  disabled={!exports?.pdf}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-white rounded-md text-xs font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${exports?.pdf ? 'bg-primary-green' : 'bg-secondary-grey'}`}
                >
                  <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                  </svg>
                  PDF
                </button>
              </div>
            </div>

            {/* Transcription Scroll Area */}
            <div className="flex-grow overflow-y-auto pr-2 space-y-6 custom-scrollbar">
              {diarization.length === 0 && !loading && !transcription && (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-60">
                  <svg className="h-16 w-16 mb-4 text-secondary-grey" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                  </svg>
                  <p className="text-gray-500 font-medium">Awaiting audio input</p>
                  <p className="text-sm text-gray-400 mt-2">Start live dictation or upload a file to begin.</p>
                </div>
              )}

              {/* Single block format if no diarization mapping but transcription exists */}
              {transcription && diarization.length === 0 && (
                <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{transcription}</p>
                </div>
              )}

              {/* Mapped Diarization Segments */}
              {sortedDiarization.map((segment, idx, arr) => {
                // Fetch the speaker ID mapped during our first pass to ensure consistency
                const speakerNum = speakerMap[segment.speaker];

                // Apply unique colors and contrast rules based on speaker index
                const style = speakerStyles[speakerNum % speakerStyles.length];
                const avatarText = `S${speakerNum}`;

                return (
                  <div key={idx} className="flex gap-4 group">
                    <div className="flex-shrink-0 relative">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm relative z-10 shadow-sm ${style.bg} ${style.text}`}
                        title={avatarText}
                      >
                        {avatarText}
                      </div>
                      {/* Vertical line connecting blocks except for the last one */}
                      {idx !== arr.length - 1 && (
                        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-px h-[calc(100%+1.5rem)] z-0 bg-secondary-grey opacity-50"></div>
                      )}
                    </div>
                    <div className="flex-grow pb-2">
                      <p className="text-xs font-semibold mb-1 text-secondary-grey">
                        {avatarText} &bull; {segment.start.toFixed(2)}s - {segment.end.toFixed(2)}s
                      </p>
                      <div className="bg-white p-4 rounded-xl rounded-tl-none border border-gray-100 shadow-sm">
                        <p className="text-sm text-gray-800 leading-relaxed">
                          {segment.text}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}