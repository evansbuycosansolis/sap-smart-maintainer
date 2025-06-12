import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";
import { pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

function App() {
  // ----- State -----
  const [isIndexing, setIsIndexing] = useState(false);
  const [showGif, setShowGif] = useState(false);
  const [globalFiles, setGlobalFiles] = useState([]);
  const [selectedTypeTop, setSelectedTypeTop] = useState(null);
  const [selectedTypeBottom, setSelectedTypeBottom] = useState(null);
  const [file, setFile] = useState(null);
  const [filename, setFilename] = useState("No file chosen");
  const [question, setQuestion] = useState("");
  const [globalQuestion, setGlobalQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [globalAnswer, setGlobalAnswer] = useState("");
  const [notification, setNotification] = useState("");
  const [showQuestionBox, setShowQuestionBox] = useState(false);
  const [loading, setLoading] = useState(false);
  const [globalLoading, setGlobalLoading] = useState(false);
  const [indexingStatus, setIndexingStatus] = useState({
    current: 0,
    total: 0,
    running: false
  });
  const [voiceMode, setVoiceMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [listeningFor, setListeningFor] = useState(null);
  const [pdfUrl, setPdfUrl] = useState("");
  const answerRef = useRef(null);
  const globalAnswerRef = useRef(null);
  const recognitionRef = useRef(null);

  // ----- Document Types -----
  const docTypes = [
    "Document Management System (DMS) Integration",
    "Maintenance Planning Documents",
    "Authorizations and Change Logs",
    "Procurement and Material Management",
    "Costing and Controlling Documents",
    "Reporting and Historical Documents",
    "Maintenance Notification Documents",
    "Work Order Documents",
  ];

  // ----- UI/UX Helpers -----
  const resetUI = () => {
    setShowGif(false);
    setNotification("");
    setAnswer("");
    setGlobalAnswer("");
    setQuestion("");
    setGlobalQuestion("");
    setFile(null);
    setFilename("No file chosen");
    setLoading(false);
    setGlobalLoading(false);
    setSelectedTypeTop(null);
    setSelectedTypeBottom(null);
    setIsListening(false);
    setListeningFor(null);
    setPdfUrl("");
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (recognitionRef.current) recognitionRef.current.abort();
    setIndexingStatus({ current: 0, total: 0, running: false });
  };

  const speakText = (text) => {
    if (!window.speechSynthesis) {
      alert("Text-to-speech not supported in this browser.");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    const voices = window.speechSynthesis.getVoices();
    utterance.voice =
      voices.find(v => v.lang.startsWith("en") && v.name.toLowerCase().includes("female")) ||
      voices.find(v => v.lang.startsWith("en") && v.gender === "female") ||
      voices.find(v => v.lang.startsWith("en")) ||
      null;
    utterance.onstart = () => setShowGif(false);
    window.speechSynthesis.speak(utterance);
  };

  const stopAll = () => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (recognitionRef.current) recognitionRef.current.abort();
    setIsListening(false);
    setShowGif(false);
  };

  // ----- Voice Input Logic -----
  const startVoiceInput = (which) => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert("Voice input not supported in this browser.");
      return;
    }
    setIsListening(true);
    setListeningFor(which);
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = true;
    let fullTranscript = "";
    recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript.trim();
        // === When user says "Go" ===
        if (/^go[\s,.!?]*$/i.test(transcript)) {
          recognition.stop();
          setShowGif(true); // Show GIF immediately
          const actualQuestion = fullTranscript.replace(/go[\s,.!?]*$/i, "").trim();
          if (which === "pdf") {
            setQuestion(actualQuestion);
            setIsListening(false);
            setShowQuestionBox(true);
            setTimeout(() => {
              const btn = document.getElementById("voice-ask-pdf");
              if (btn) btn.click();
            }, 350);
          } else if (which === "global") {
            setGlobalQuestion(actualQuestion);
            setIsListening(false);
            setTimeout(() => {
              const btn = document.getElementById("voice-ask-global");
              if (btn) btn.click();
            }, 350);
          }
          setShowGif(false);
          fullTranscript = "";
          return;
        }
        fullTranscript += transcript + " ";
      }
      fullTranscript = fullTranscript.trim();
    };
    recognition.onerror = (event) => {
      setIsListening(false);
      setShowGif(false);
      alert('Voice recognition error: ' + event.error);
    };
    recognition.onend = () => {
      setIsListening(false);
    };
    recognition.start();
    recognitionRef.current = recognition;
  };

  // ----- Indexing Status Polling -----
  useEffect(() => {
    let interval;
    const fetchStatus = async () => {
      try {
        const res = await axios.get("http://localhost:8080/api/indexing-status/");
        setIndexingStatus(res.data);
      } catch (e) {
        setIndexingStatus({ current: 0, total: 0, running: false });
      }
    };
    fetchStatus();
    if (indexingStatus.running) {
      interval = setInterval(fetchStatus, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [indexingStatus.running]);

  // ----- Scroll to Answers on Update -----
  useEffect(() => {
    if (answer && answerRef.current) {
      answerRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      if (voiceMode && answer) {
        setTimeout(() => speakText(answer), 400);
      }
    }
  }, [answer, voiceMode]);

  useEffect(() => {
    if (globalAnswer && globalAnswerRef.current) {
      globalAnswerRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
      if (voiceMode && globalAnswer) {
        setTimeout(() => speakText(globalAnswer), 400);
      }
    }
  }, [globalAnswer, voiceMode]);

  useEffect(() => {
    if ('speechSynthesis' in window) window.speechSynthesis.getVoices();
  }, []);

  // ----- Auto-dismiss notification -----
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(""), 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  // ----- Upload, Reindex, and Ask Handlers -----
  const handleUpload = async () => {
    if (!file) return alert("Please choose a PDF first.");
    if (!selectedTypeTop) return alert("Please select a document type first!");
    if (file.type !== "application/pdf") return alert("Please upload a valid PDF file.");
    const formData = new FormData();
    formData.append("pdf", file);
    formData.append("category", selectedTypeTop);
    try {
      setLoading(true);
      setNotification("");
      const res = await axios.post("http://localhost:8080/api/upload-pdf/", formData);
      if (res.data && res.data.message) {
        setNotification("PDF uploaded successfully! Now ask a question below.");
        setShowQuestionBox(true);
      } else {
        setNotification(res.data.error || "Failed to upload PDF.");
        setShowQuestionBox(false);
      }
    } catch (error) {
      setNotification(error.response?.data?.error || error.message || "Failed to upload PDF.");
      setShowQuestionBox(false);
    } finally {
      setLoading(false);
    }
  };

  const handleReindex = async () => {
    setIsIndexing(true);
    try {
      await axios.post("http://localhost:8080/api/reindex-pdfs/");
      alert("Re-indexing started! You'll see new results after it completes.");
    } catch (err) {
      alert("Failed to start re-indexing!");
    }
    setIsIndexing(false);
  };

  const handleAsk = async (e) => {
    if (e) e.preventDefault();
    if (!question.trim()) {
      setShowGif(false);
      setNotification("Enter a question.");
      return;
    }
    if (!file) {
      setShowGif(false);
      setNotification("Please upload a PDF first.");
      return;
    }
    if (!selectedTypeTop) {
      setShowGif(false);
      setNotification("Please select a document type!");
      return;
    }
    try {
      setLoading(true);
      setShowGif(true);
      setNotification("");
      const res = await axios.post(
        "http://localhost:8080/api/ask-pdf/",
        { question, filename: file.name, category: selectedTypeTop },
        { headers: { "Content-Type": "application/json" } }
      );
      setAnswer(typeof res.data.answer === "string"
        ? res.data.answer
        : JSON.stringify(res.data.answer, null, 2));
      setQuestion("");
      // ---- Use the presigned URL instead of S3_BASE_URL ----
      const url = await fetchPresignedUrl(file.name, selectedTypeTop);
      setPdfUrl(url);
    } catch (error) {
      setNotification("Failed to ask the question.");
    } finally {
      setLoading(false);
      setShowGif(false);
    }
  };

  const handleAskAll = async (e) => {
    if (e) e.preventDefault();
    if (!globalQuestion.trim()) {
      setShowGif(false);
      setNotification("Enter a question.");
      return;
    }
    if (!selectedTypeBottom) {
      setShowGif(false);
      setNotification("Please select a document type!");
      return;
    }
    try {
      setGlobalLoading(true);
      setShowGif(true);
      setNotification("");
      const res = await axios.post(
        "http://localhost:8080/api/ask-all-pdfs/",
        {
          question: globalQuestion,
          category: selectedTypeBottom,
        },
        { headers: { "Content-Type": "application/json" } }
      );
      setGlobalAnswer(res.data.answer || "No answer was generated.");
      setGlobalFiles(res.data.files || []);
      setGlobalQuestion(""); // CLEAR after answer
    } catch (error) {
      setNotification("Failed to ask global question.");
      setGlobalFiles([]);
      setGlobalQuestion("");
    } finally {
      setGlobalLoading(false);
      setShowGif(false);
    }
  };

  // ----- Presigned PDF URL -----
  async function fetchPresignedUrl(filename, folder) {
    const params = new URLSearchParams({ filename, folder });
    const res = await fetch(`/api/pdf-link/?${params.toString()}`);
    const data = await res.json();
    return data.url; // Use this as the PDF link!
  }

  // ----- Render -----
  return (
    <div className="main-bg">
      {showGif && (
        <div className="overlay-loader">
          <img src="/logo192.png" alt="Searching..." className="loader-gif" />
        </div>
      )}
      {/* Toast Notification */}
      {notification && (
        <div className="toast">
          {notification}
          <button className="toast-close" onClick={() => setNotification("")}>×</button>
        </div>
      )}
      <div className="container">
        {/* ===== Voice mode toggle ===== */}
        <div className="voice-toggle-row">
          <label className="voice-label">
            <input
              type="checkbox"
              checked={voiceMode}
              onChange={e => setVoiceMode(e.target.checked)}
              className="voice-checkbox"
              aria-label="Toggle Voice Mode"
            />
            Voice Mode
          </label>
          <button
            className="re-index-btn"
            style={{ marginLeft: "16px" }}
            onClick={handleReindex}
            disabled={isIndexing}
          >
            {isIndexing ? "Indexing..." : "Re-Index PDFs"}
          </button>
        </div>
        {/* ===== Indexing Progress Bar ===== */}
        {indexingStatus.running && (
          <div className="indexing-bar">
            <div className="spinner"></div>
            <span>
              {indexingStatus.total
                ? `Indexing PDFs... (${indexingStatus.current}/${indexingStatus.total})`
                : "Indexing PDFs, please wait..."}
            </span>
            {indexingStatus.total > 0 && (
              <progress
                max={indexingStatus.total}
                value={indexingStatus.current}
                className="progress-bar"
              />
            )}
          </div>
        )}
        {/* ===== PDF Viewer ===== */}
        {pdfUrl && (
          <div className="pdf-viewer-section">
            <h3>Currently Queried PDF:</h3>
            <iframe
              src={pdfUrl}
              title="Queried PDF"
              width="100%"
              height="450"
              className="pdf-iframe"
            />
            <div>
              <a href={pdfUrl} target="_blank" rel="noopener noreferrer" className="pdf-link">
                Open PDF in New Tab
              </a>
            </div>
          </div>
        )}
        {/* ===== PDF Upload/Q&A (Single PDF) ===== */}
        <div className="card">
          <h1>Ask LLM about this PDF</h1>
          <div className="upload-section">
            <div className="doc-type-grid">
              {docTypes.map((type) => (
                <button
                  key={type}
                  className={`doc-type-btn ${selectedTypeTop === type ? "selected" : ""}`}
                  onClick={() => setSelectedTypeTop(type)}
                  type="button"
                >
                  {type}
                </button>
              ))}
            </div>
            <div className="file-upload-row" style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => {
                  setFile(e.target.files[0]);
                  setFilename(e.target.files[0]?.name || "No file chosen");
                }}
                id="pdf-upload"
                style={{ marginRight: "8px" }}
              />
              <span className="filename">{filename}</span>
              <button className="upload-btn" onClick={handleUpload} disabled={loading} aria-label="Upload PDF">
                {loading ? "Uploading..." : "Upload PDF"}
              </button>
            </div>
          </div>
        </div>
        <div className="card question-section">
          {showQuestionBox && (
            <form onSubmit={handleAsk} className="question-form">
              <label htmlFor="question-input">Ask a question about this PDF:</label>
              <div className="question-row">
                <textarea
                  id="question-input"
                  value={question}
                  placeholder={voiceMode ? 'Click mic and speak, then say "Go"...' : "Enter your question..."}
                  onChange={e => setQuestion(e.target.value)}
                  rows={2}
                  className="question-input"
                  disabled={voiceMode && isListening}
                />
                {voiceMode && (
                  <>
                    <button
                      type="button"
                      title={isListening ? "Listening..." : "Speak your question (end with 'Go')"}
                      onClick={() => !isListening && startVoiceInput("pdf")}
                      className="mic-btn"
                      disabled={isListening}
                    >
                      {isListening && listeningFor === "pdf" ? "🎙️" : "🎤"}
                    </button>
                    <button
                      type="button"
                      title="Stop talking or listening"
                      onClick={stopAll}
                      className="stop-btn"
                    >
                      🛑
                    </button>
                  </>
                )}
              </div>
              {!voiceMode && (
                <button type="submit" className="ask-btn" disabled={loading}>
                  {loading ? "Asking..." : "Ask"}
                </button>
              )}
              {voiceMode && (
                <button
                  type="submit"
                  id="voice-ask-pdf"
                  style={{ display: "none" }}
                  tabIndex={-1}
                  aria-hidden="true"
                >
                  Ask
                </button>
              )}
            </form>
          )}
          {answer && (
            <div className="answer-container" ref={answerRef}>
              <h3>Answer:</h3>
              <div className="answer-box">
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{answer}</pre>
                {!voiceMode && (
                  <button
                    type="button"
                    onClick={() => speakText(answer)}
                    title="Listen to answer"
                    className="tts-btn"
                  >
                    🔊
                  </button>
                )}
                <button
                  className="clear-btn"
                  onClick={() => setAnswer("")}
                  style={{ marginLeft: 16, marginTop: 8 }}
                  type="button"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>

        <hr className="divider" />

        {/* ===== Global PDF Q&A Section ===== */}
        <div className="card question-section global">
          <h1>Ask LLM anything across all stored PDFs</h1>
          <div className="doc-type-grid">
            {docTypes.map((type) => (
              <button
                key={type}
                className={`doc-type-btn ${selectedTypeBottom === type ? "selected" : ""}`}
                onClick={() => setSelectedTypeBottom(type)}
                type="button"
              >
                {type}
              </button>
            ))}
          </div>
          <form onSubmit={handleAskAll} className="question-form">
            <div className="question-row">
              <textarea
                value={globalQuestion}
                placeholder={voiceMode ? 'Click mic and speak, then say "Go"...' : "Enter your question..."}
                onChange={e => setGlobalQuestion(e.target.value)}
                rows={1}
                className="question-input"
                disabled={voiceMode && isListening}
              />
              {voiceMode && (
                <>
                  <button
                    type="button"
                    title={isListening ? "Listening..." : "Speak your question (end with 'Go')"}
                    onClick={() => !isListening && startVoiceInput("global")}
                    className="mic-btn"
                    disabled={isListening}
                  >
                    {isListening && listeningFor === "global" ? "🎙️" : "🎤"}
                  </button>
                  <button
                    type="button"
                    title="Stop talking or listening"
                    onClick={stopAll}
                    className="stop-btn"
                  >
                    🛑
                  </button>
                </>
              )}
            </div>
            {!voiceMode && (
              <button type="submit" className="ask-btn" disabled={globalLoading || !selectedTypeBottom}>
                {globalLoading ? "Searching..." : "Ask All"}
              </button>
            )}
            {voiceMode && (
              <button
                type="submit"
                id="voice-ask-global"
                style={{ display: "none" }}
                tabIndex={-1}
                aria-hidden="true"
              >
                Ask All
              </button>
            )}
          </form>
        </div>
        {/* ===== Global Answer Box ===== */}
        {globalAnswer && (
          <div className="card answer-container" ref={globalAnswerRef}>
            <div className="answer-box">
              <h3 style={{ marginBottom: "5px", color: "#16ff40" }}>Global Answer:</h3>
              <pre
                className="global-answer-pre"
                style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
              >
                {globalAnswer}
              </pre>
              {!voiceMode && (
                <button
                  type="button"
                  onClick={() => speakText(globalAnswer)}
                  title="Listen to answer"
                  className="tts-btn"
                >
                  🔊
                </button>
              )}
              <button
                className="clear-btn"
                onClick={() => setGlobalAnswer("")}
                style={{ marginLeft: 16, marginTop: 8 }}
                type="button"
              >
                Clear
              </button>
            </div>
          </div>
        )}

        {/* ====== Global PDF List ====== */}
        {globalFiles && globalFiles.length > 0 && (
          <div className="card global-pdf-list">
            <div className="pdf-list-title">
              The answer was taken from one or more of these {globalFiles.length} PDFs under the label: <span className="pdf-list-label">{selectedTypeBottom}</span>
            </div>
            <ul className="pdf-list-ul">
              {globalFiles.map((fname) => (
                <li key={fname}>
                  <button
                    type="button"
                    className="pdf-link-btn"
                    onClick={async () => {
                      const url = await fetchPresignedUrl(fname, selectedTypeBottom);
                      window.open(url, "_blank");
                    }}
                    style={{
                      background: "none",
                      border: "none",
                      color: "#44aaff",
                      textDecoration: "underline",
                      cursor: "pointer",
                      padding: 0,
                      font: "inherit",
                    }}
                  >
                    {fname}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
