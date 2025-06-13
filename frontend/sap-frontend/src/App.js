import React, { useState, useEffect, useRef, useMemo } from "react";
import axios from "axios";
import "./App.css";
import { pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";


// Set PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

function App() {


  // ===========================================================================================
  // =============== helper functions===========================================================
  // ===========================================================================================


  // ----- General State -----
  const recognitionRef = useRef(null);
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
  const [predictiveFile, setPredictiveFile] = useState(null);
const [predictiveQuestion, setPredictiveQuestion] = useState("");
const [predictiveAnalysis, setPredictiveAnalysis] = useState("");

  const [indexingStatus, setIndexingStatus] = useState({
    current: 0,
    total: 0,
    running: false
  });

  async function uploadPredictivePDF(pdfFile, question) {
  const formData = new FormData();
  formData.append("pdf", pdfFile);
  if (question) formData.append("question", question);

  try {
    const response = await axios.post(
      "http://localhost:8080/api/predictive-analyze/",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" }
      }
    );
    // Success: response.data contains your LLM output!
    return response.data;
  } catch (err) {
    // Handle error, e.g., display error message
    console.error(err);
    throw err;
  }
  }

async function handlePredictiveUpload() {
  try {
    setLoading(true); // optional: show spinner
    const result = await uploadPredictivePDF(predictiveFile, predictiveQuestion);
    setPredictiveAnalysis(result); // or however you store/display the output
  } catch (err) {
    setPredictiveAnalysis("Upload or analysis failed!");
  } finally {
    setLoading(false);
  }
}

  const [voiceMode, setVoiceMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [listeningFor, setListeningFor] = useState(null);
  const [pdfUrl, setPdfUrl] = useState("");

  // ----- Refs -----
  const answerRef = useRef(null);
  const globalAnswerRef = useRef(null);


  // --- Predictive Analysis States/Handlers ---
  const [selectedFile, setSelectedFile] = useState(null);
  const [userQuery, setUserQuery] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);
  //const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);


  const handleVoiceInput = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Speech recognition not supported in this browser.");
      return;
    }
    if (!recognitionRef.current) {
      const SpeechRecognition = window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";
      recognition.onresult = (event) => {
        setUserQuery(event.results[0][0].transcript);
        setListening(false);
      };
      recognition.onend = () => setListening(false);
      recognitionRef.current = recognition;
    }

    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      recognitionRef.current.start();
      setListening(true);
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleSendQuery = async () => {
    setError("");
    setAnalysisResult(null);
    if (!selectedFile) {
      setError("Please upload a sensor log PDF.");
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("pdf", selectedFile);
      formData.append("question", userQuery || "");
      const res = await axios.post("/api/predictive-analyze/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setAnalysisResult(res.data);
      if (res.data) {
      setSelectedFile(null);
      setUserQuery("");
      }
    } catch (err) {
      setError(
        err?.response?.data?.error ||
        err.message ||
        "Failed to analyze asset status."
      );
    }
    setLoading(false);
  };


  function riskColor(score) {
  if (score == null) return "none";
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "medium";
  return "low";
}


  const toggleVoiceInput = () => {
  if (!recognitionRef.current) {
    alert("Voice recognition is not initialized. Please use the microphone button to start.");
    return;
  }
  if (listening) {
    recognitionRef.current.stop();
    setListening(false);
  } else {
    recognitionRef.current.start();
    setListening(true);
  }
  };

  // ----- Filtering State -----
  const [selectedAsset, setSelectedAsset] = useState("");
  const [selectedFailure, setSelectedFailure] = useState("");
  const [selectedTech, setSelectedTech] = useState("");

  // define results as an empty array here.
  const [results, setResults] = useState([]);

  // ----- Metadata Collections for Dropdowns -----
  const uniqueAssets = useMemo(
    () => Array.from(new Set(results.map(r => r.metadata.asset_id).filter(Boolean))),
    [results]
  );
  const uniqueFailures = useMemo(
    () => Array.from(new Set(results.map(r => r.metadata.failure_type).filter(Boolean))),
    [results]
  );
  const uniqueTechs = useMemo(
    () => Array.from(new Set(results.map(r => r.metadata.handled_by).filter(Boolean))),
    [results]
  );

  // ----- Filtering Logic -----
  const filteredResults = useMemo(
    () =>
      results.filter(
        item =>
          (!selectedAsset || item.metadata.asset_id === selectedAsset) &&
          (!selectedFailure || item.metadata.failure_type === selectedFailure) &&
          (!selectedTech || item.metadata.handled_by === selectedTech)
      ),
    [results, selectedAsset, selectedFailure, selectedTech]
  );


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

  /* ----- UI/UX Helpers -----
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
  };*/
function speakText(text, onDone) {
  if (!window.speechSynthesis) {
    alert("Text-to-speech not supported in this browser.");
    return;
  }
  // Stop any ongoing speech
  window.speechSynthesis.cancel();

  // Get voices, but handle the async population on first load
  const pickVoice = () => {
    const voices = window.speechSynthesis.getVoices();
    return (
      voices.find(v => v.lang.startsWith("en") && v.name.toLowerCase().includes("female")) ||
      voices.find(v => v.lang.startsWith("en") && v.gender === "female") ||
      voices.find(v => v.lang.startsWith("en")) ||
      null
    );
  };

  const speakNow = () => {
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.voice = pickVoice();
    utterance.onend = () => {
      if (onDone) onDone();
      // Optionally hide your GIF/animation here
      // setShowGif(false);
    };
    // Optionally show your GIF/animation here
    // setShowGif(true);
    window.speechSynthesis.speak(utterance);
  };

  // If no voices yet, wait for them to load
  if (window.speechSynthesis.getVoices().length === 0) {
    window.speechSynthesis.onvoiceschanged = speakNow;
  } else {
    speakNow();
  }
}

// Usage example:
// speakText("Asset predictive analysis complete. Risk score is high.");


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



  // ===========================================================================================
  // =============== useEffect==================================================================
  // ===========================================================================================

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




// As soon as predictiveAnalysis gets new data, your app will auto-speak the summary
const lastSpoken = useRef(""); // tracks last spoken value

useEffect(() => {
  // Realistic checks—add or adjust as needed for your data
  const ready =
    predictiveAnalysis &&
    typeof predictiveAnalysis === "object" &&
    predictiveAnalysis.ml_result &&
    typeof predictiveAnalysis.ml_result.risk_score === "number" &&
    predictiveAnalysis.ml_result.predicted_failure &&
    predictiveAnalysis.ml_result.recommendation; // customize as needed
  if (!ready) return; // Don't say anything if not ready
  // Summarize
  const summary = getPredictiveSummary(predictiveAnalysis);
  // Only speak if summary is new and non-empty (not a default like "No analysis available.")
  if (
    summary &&
    summary.trim().toLowerCase() !== "no" &&
    summary.trim().toLowerCase() !== "no analysis available." &&
    summary !== lastSpoken.current
  ) {
    speakSummary(summary);
    lastSpoken.current = summary;
  }
}, [predictiveAnalysis]);
  // ----- auto-read aloud (for accessibility/voice mode): -----
  useEffect(() => {
  if (analysisResult && voiceMode && 'speechSynthesis' in window) {
    const msg = new window.SpeechSynthesisUtterance(JSON.stringify(analysisResult));
    window.speechSynthesis.speak(msg);
  }
}, [analysisResult, voiceMode]);


// instead of reading the full JSON
const message = analysisResult?.analysis
  ? `Predicted failure: ${analysisResult.analysis.predicted_failure || "None"}.
    Risk score: ${analysisResult.analysis.risk_score || "N/A"}.
    Recommendation: ${analysisResult.analysis.recommendation || ""}.
    Action: ${analysisResult.action || ""}`
  : JSON.stringify(analysisResult);

const msg = new window.SpeechSynthesisUtterance(message);
window.speechSynthesis.speak(msg);

function getPredictiveSummary(analysis) {
 if (!analysis || !analysis.ml_result || !analysis.ml_result.risk_score) return ""; // return blank
  return (
    `Asset risk score is ${analysis.ml_result.risk_score}. ` +
    `Predicted failure: ${analysis.ml_result.predicted_failure || 'None'}. ` +
    `Recommended action: ${analysis.ml_result.recommendation || 'No recommendation.'}`
  );
}

function speakSummary(text) {
  if ('speechSynthesis' in window) {
    const utterance = new window.SpeechSynthesisUtterance(text);
    // Optional: Set voice/language/rate/etc.
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
  } else {
    alert('Sorry, your browser does not support speech synthesis.');
  }
}


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

// Shows only results matching the same failure type
function handleShowSimilarFailures(failureType) {
  setSelectedFailure(failureType);
}

// Shows the most recent technician for this asset/failure type
function handleWhoSolvedLast(metadata) {
  // Find all results matching the same asset or failure type
  const matches = results
    .filter(item =>
      (metadata.asset_id && item.metadata.asset_id === metadata.asset_id) ||
      (metadata.failure_type && item.metadata.failure_type === metadata.failure_type)
    )
    // Sort by date, most recent first (assumes 'date' is in YYYY-MM-DD format)
    .sort((a, b) => (b.metadata.date || "").localeCompare(a.metadata.date || ""));

  if (matches.length > 0) {
    const lastTech = matches[0].metadata.handled_by || "Unknown";
    alert(`Most recent technician: ${lastTech}`);
  } else {
    alert("No similar records found.");
  }
}





  // =====================================================================================================
  // ====================== RENDER =======================================================================
  // =====================================================================================================
return (
  <div className="main-bg">
    {/* Loader */}
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



      {/* ===== Voice mode toggle & Re-Index ===== */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 24, marginBottom: 12 }}>
        <label className="voice-label" style={{ fontWeight: 500, fontSize: "1.08rem" }}>
          <input
            type="checkbox"
            checked={voiceMode}
            onChange={e => setVoiceMode(e.target.checked)}
            className="voice-checkbox"
            aria-label="Toggle Voice Mode"
            style={{ marginRight: 4 }}
          />
          Voice Mode
        </label>
        <button
          className="re-index-btn"
          style={{ marginLeft: 6, fontWeight: 500, background: "#02fd98", color: "#111", border: "none", borderRadius: 6, padding: "5px 18px", fontSize: "1rem" }}
          onClick={handleReindex}
          disabled={isIndexing}
        >
          {isIndexing ? "Indexing..." : "Re-Index PDFs"}
        </button>
      </div>





      {/* ===== PDF Upload/Q&A (Single PDF) ===== */}
      <div className="card" style={{ marginBottom: 36, marginTop: 10, background: "#14181e" }}>
        <h1 style={{ marginBottom: 16, marginTop: 0, fontWeight: 700 }}>Ask LLM about this PDF</h1>
        <div className="upload-section">
          <div className="doc-type-grid" style={{ marginBottom: 14 }}>
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
            <div className="file-upload-row" style={{ display: "flex", justifyContent: "center", alignItems: "center", marginTop: 10 }}>
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
              <button className="upload-btn" onClick={handleUpload} disabled={loading} aria-label="Upload PDF" style={{ marginLeft: 10, background: "#02fd98", color: "#111" }}>
                {loading ? "Uploading..." : "Upload PDF"}
              </button>
            </div>

            {/* ===== QUESTION ROW WITH VOICE CONTROLS ===== */}
            <div className="question-row" style={{ display: "flex", alignItems: "center", marginTop: 18 }}>
              <textarea
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder={voiceMode ? 'Click mic and speak, then say "Go"...' : "Enter your question..."}
                rows={2}
                className="question-input"
                disabled={voiceMode && isListening}
                style={{ flex: 1, minWidth: 0 }}
              />
              {voiceMode && (
                <>
                  <button
                    type="button"
                    title={isListening ? "Listening..." : "Speak your question (end with 'Go')"}
                    onClick={() => !isListening && startVoiceInput("pdf")}
                    className="mic-btn"
                    disabled={isListening}
                    style={{ marginLeft: 8 }}
                  >
                    {isListening && listeningFor === "pdf" ? "🎙️" : "🎤"}
                  </button>
                  <button
                    type="button"
                    title="Stop talking or listening"
                    onClick={stopAll}
                    className="stop-btn"
                    style={{ marginLeft: 4 }}
                  >
                    🛑
                  </button>
                </>
              )}
              {!voiceMode && (
                <button
                  type="button"
                  className="ask-btn"
                  onClick={handleAsk}
                  disabled={loading}
                  style={{ marginLeft: 10, background: "#02fd98", color: "#111" }}
                >
                  {loading ? "Asking..." : "Ask"}
                </button>
              )}
            </div>
        </div>
      </div>









      {/* ===== Global PDF Q&A Section ===== */}
      <div className="card question-section global" style={{ padding: "40px 24px 32px 24px", background: "#14181e", marginBottom: 28 }}>
        <h1 style={{
          fontSize: "2.0rem",
          fontWeight: 700,
          marginBottom: 20,
          marginTop: 0,
          color: "#fff",
          textShadow: "0 2px 8px #000c"
        }}>
          Ask LLM anything across all stored PDFs
        </h1>
        <div className="doc-type-grid" style={{ marginBottom: 22 }}>
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

        {/* Filters & Ask All on one row */}
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", marginBottom: 8 }}>
          <select value={selectedAsset} onChange={e => setSelectedAsset(e.target.value)}
            style={{ fontSize: "1rem", borderRadius: 4, background: "#23272e", color: "#fff", border: "1px solid #555", padding: 4, marginRight: 2 }}>
            <option value="">All Assets</option>
            {uniqueAssets.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <select value={selectedFailure} onChange={e => setSelectedFailure(e.target.value)}
            style={{ fontSize: "1rem", borderRadius: 4, background: "#23272e", color: "#fff", border: "1px solid #555", padding: 4, marginLeft: 2, marginRight: 2 }}>
            <option value="">All Failure Types</option>
            {uniqueFailures.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
          <select value={selectedTech} onChange={e => setSelectedTech(e.target.value)}
            style={{ fontSize: "1rem", borderRadius: 4, background: "#23272e", color: "#fff", border: "1px solid #555", padding: 4, marginLeft: 2 }}>
            <option value="">All Technicians</option>
            {uniqueTechs.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <button
            type="button"
            className="ask-btn"
            style={{
              fontWeight: "bold",
              marginLeft: 18,
              background: "#02fd98",
              color: "#111",
              border: "none",
              borderRadius: 80,
              fontSize: "1.18rem",
              padding: "5px 34px",
              boxShadow: "0 2px 6px #1115"
            }}
            onClick={handleAskAll}
            disabled={globalLoading || !selectedTypeBottom}
          >
          Send Query
          </button>
        </div>
        {/* Question Textarea */}
        <form onSubmit={handleAskAll} style={{ width: "100%" }}>
          <div className="question-row">
            <textarea
              value={globalQuestion}
              placeholder={voiceMode ? 'Click mic and speak, then say "Go"...' : "Enter your question..."}
              onChange={e => setGlobalQuestion(e.target.value)}
              rows={2}
              className="question-input"
              style={{
                width: "100%",
                marginTop: 8,
                fontSize: "1.05rem",
                borderRadius: 7,
                border: "1px solid #444",
                background: "#191c22",
                color: "#f8f8f8",
                padding: 12,
                resize: "none",
                fontFamily: "Fira Mono, Menlo, monospace"
              }}
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
        <div className="card answer-container" ref={globalAnswerRef} style={{ marginTop: 18, background: "#181d23", color: "#fff", borderRadius: 10, border: "1px solid #202328", padding: "24px 18px 20px 18px" }}>
          <div className="answer-box">
            <h3 style={{ marginBottom: "8px", color: "#16ff40", fontSize: "1.3rem", fontWeight: 700 }}>Global Answer:</h3>
            <pre
              className="global-answer-pre"
              style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: "1.08rem", fontFamily: "Fira Mono, Menlo, monospace" }}
            >
              {globalAnswer}
            </pre>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 18 }}>
              {!voiceMode && (
                <button
                  type="button"
                  onClick={() => speakText(globalAnswer)}
                  title="Listen to answer"
                  className="tts-btn"
                  style={{ background: "#222", color: "#fff", fontSize: "1.4rem", border: "none", borderRadius: 5, padding: "6px 12px" }}
                >
                  🔊
                </button>
              )}
              <button
                className="clear-btn"
                onClick={() => setGlobalAnswer("")}
                style={{
                  marginLeft: 12,
                  marginTop: 0,
                  background: "#1c2027",
                  color: "#f36",
                  border: "1px solid #333",
                  borderRadius: 8,
                  fontWeight: 600,
                  fontSize: "1.08rem",
                  padding: "6px 22px"
                }}
                type="button"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Other sections:Place here first, before merging to final codes above */}

{/* --- Predictive Analysis Section --- */} 
<div className="section predictive-analysis">
  <h1>Ask LLM about its Analysis on Asset Status</h1>
  <div className="upload-row">
    <input
      type="file"
      accept="application/pdf"
      onChange={e => setPredictiveFile(e.target.files[0])}
    />
    <span style={{ marginLeft: 10 }}>
      {predictiveFile ? predictiveFile.name : "No file chosen"}
    </span>
    <button
      onClick={handlePredictiveUpload}
      disabled={loading || !predictiveFile}
    >
      {loading ? "Analyzing..." : "Upload Data Sheet & Send Query"}
    </button>
  </div>
  <div className="query-box">
    <textarea
      placeholder="Enter your analysis query (optional)..."
      value={predictiveQuestion}
      onChange={e => setPredictiveQuestion(e.target.value)}
    />
    <button
      onClick={handlePredictiveUpload}
      disabled={loading || !predictiveFile}
    >
      {loading ? "Analyzing..." : "Send Query"}
    </button>
    <button onClick={handleVoiceInput} disabled={!("webkitSpeechRecognition" in window)}>
      {listening ? "🎤 Stop" : "🎤 Speak"}
    </button>
  </div>
  <div className="analysis-output">
    <h4>LLM Predictive Analysis</h4>
    {error && <div style={{ color: "red" }}>{error}</div>}
    {!predictiveAnalysis && !error && <div>No analysis yet.</div>}
  </div>


  {/* --- Display Result Nicely --- */}
{predictiveAnalysis && (
  <div className="predictive-summary">
    <h3>Asset Predictive Analysis Result</h3>
       <button
        style={{ marginTop: 12, marginBottom: 8 }}
        onClick={() => speakSummary(getPredictiveSummary(predictiveAnalysis))}
      >
        🔊 Speak Summary
      </button>

    <div className="predictive-core">
      <div>
        <span className="predictive-label">Risk Score:</span>
        <span className={`risk-badge risk-${riskColor(predictiveAnalysis.ml_result?.risk_score)}`}>
          {predictiveAnalysis.ml_result?.risk_score ?? ""}
        </span>
      </div>
      <div>
        <span className="predictive-label">Predicted Failure:</span>
        <b>{predictiveAnalysis.ml_result?.predicted_failure ?? ""}</b>
      </div>
      <div>
        <span className="predictive-label">Recommendation:</span>
        <b>{predictiveAnalysis.ml_result?.recommendation ?? ""}</b>
      </div>
      <div>
        <span className="predictive-label">Action:</span>
        <b>{predictiveAnalysis.action ?? ""}</b>
      </div>
    </div>
 
    <details className="context-details">
      <summary>
        Show Asset Maintenance Context ({predictiveAnalysis.context_docs?.length || 0} records)
      </summary>

      <div className="context-list-scroll">
        <ul>
          {(predictiveAnalysis.context_docs || []).map((doc, idx) => {
            // Fallbacks in case some fields are missing
            const meta = doc.metadata || {};
            const assetId = meta.asset_id ?? "";
            const date = meta.date ?? "";
            // Clean up failure_type and handled_by
            let failureType = meta.failure_type || "";
            if (failureType && typeof failureType === "string") {
              failureType = failureType.replace(/\nHandled By.*/i, "");
            }
            let handledBy = meta.handled_by || "";
            if (handledBy && typeof handledBy === "string") {
              handledBy = handledBy.split("\nActions")[0].replace(/^By:\s*/, "");
            }
            // Take first two lines of the content for preview
            const contentPreview = doc.page_content
              ? doc.page_content.split('\n').slice(0, 2).join(' ')
              : "";

            return (
              <li key={doc.id || idx} style={{marginBottom: 10}}>
                <strong>
                  {assetId} [{date}]
                </strong>
                {failureType !== "" && <>: {failureType}</>}
                <br />
                {handledBy && (
                  <em>Handled By: {handledBy}</em>
                )}
                {contentPreview && (
                  <><br /><small>{contentPreview}</small></>
                )}
              </li>
            );
          })}
        </ul>
      </div>


    </details>
  </div>
)}

</div>





 {/* =================== ends here==============================  */}
    </div>
  </div>
);

}

export default App;
