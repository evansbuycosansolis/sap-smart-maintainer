// frontend/sap-frontend/src/App.js

import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

function App() {
  // Refs for auto-scrolling
  const answerRef = useRef(null);
  const globalAnswerRef = useRef(null);

  // State
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

  // Indexing progress bar state (from backend polling)
  const [indexingStatus, setIndexingStatus] = useState({
    current: 0,
    total: 0,
    running: false
  });

  // Poll backend for indexing status (Simplified)
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
    // eslint-disable-next-line
  }, [indexingStatus.running]);

  // Auto-scroll to answer when it updates
  useEffect(() => {
    if (answer && answerRef.current) {
      answerRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [answer]);

  useEffect(() => {
    if (globalAnswer && globalAnswerRef.current) {
      globalAnswerRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [globalAnswer]);

  const docTypes = [
    "Maintenance Notification Documents",
    "Costing and Controlling Documents",
    "Maintenance Planning Documents",
    "Reporting and Historical Documents",
    "Work Order Documents",
    "Authorizations and Change Logs",
    "Procurement and Material Management",
    "Document Management System (DMS) Integration"
  ];

  // ===== Upload Handler: Send doc type! =====
  const handleUpload = async () => {
    if (!file) return alert("Please choose a PDF first.");
    if (!selectedTypeTop) return alert("Please select a document type first!");
    if (file.type !== "application/pdf") return alert("Please upload a valid PDF file.");

    const formData = new FormData();
    formData.append("pdf", file);
    formData.append("category", selectedTypeTop);

    try {
      setLoading(true);
      const res = await axios.post("http://localhost:8080/api/upload-pdf/", formData);
      if (res.data && res.data.message) {
        setNotification("PDF uploaded successfully! Now ask a question below.");
        setShowQuestionBox(true);
      } else {
        setNotification(res.data.error || "Failed to upload PDF.");
        setShowQuestionBox(false);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setNotification("Failed to upload PDF.");
      setShowQuestionBox(false);
    } finally {
      setLoading(false);
    }
  };

  // ===== Single PDF Ask =====
  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return alert("Enter a question.");
    if (!file) return alert("Please upload a PDF first.");
    if (!selectedTypeTop) return alert("Please select a document type!");

    try {
      setLoading(true);
      const res = await axios.post(
        "http://localhost:8080/api/ask-pdf/",
        {
          question,
          filename: file.name,
          category: selectedTypeTop,
        },
        { headers: { "Content-Type": "application/json" } }
      );

      setAnswer(
        typeof res.data.answer === "string"
          ? res.data.answer
          : JSON.stringify(res.data.answer, null, 2)
      );
    } catch (error) {
      console.error("Ask error:", error);
      setAnswer(
        error.response?.data?.error ||
        "Something went wrong while processing your question."
      );
    } finally {
      setLoading(false);
    }
  };

  // ===== Global (All PDFs in Category) Ask =====
  const handleAskAll = async (e) => {
    e.preventDefault();
    if (!globalQuestion.trim()) return alert("Enter a global question.");
    if (!selectedTypeBottom) return alert("Select a document type!");

    try {
      setGlobalLoading(true);
      const res = await axios.post(
        "http://localhost:8080/api/ask-all-pdfs/",
        {
          question: globalQuestion,
          category: selectedTypeBottom,
        },
        { headers: { "Content-Type": "application/json" } }
      );
      setGlobalAnswer(res.data.answer || "No answer was generated.");
    } catch (error) {
      console.error("Global ask error:", error);
      setGlobalAnswer(
        error.response?.data?.error ||
        "Something went wrong while processing your global question."
      );
    } finally {
      setGlobalLoading(false);
    }
  };

  // ===== Reset form after file upload/change =====
  const resetUI = () => {
    setNotification("");
    setAnswer("");
    setShowQuestionBox(false);
    setQuestion("");
    setIndexingStatus({ current: 0, total: 0, running: false }); // Auto-reset progress
  };

  return (
    <div className="container">
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
              style={{ width: '200px', marginLeft: '16px', verticalAlign: 'middle' }}
            />
          )}
        </div>
      )}

      {/* ===== PDF Upload/Q&A (Single PDF) ===== */}
      <h1>Ask LLM about this PDF</h1>
      <div className="upload-section">
        {/* Category Selector for Upload (TOP) */}
        <div className="doc-type-grid" style={{ marginBottom: "1rem" }}>
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
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => {
            setFile(e.target.files[0]);
            setFilename(e.target.files[0]?.name || "No file chosen");
            resetUI();
          }}
        />
        <span className="filename">{filename}</span>
        <button className="upload-btn" onClick={handleUpload} disabled={loading}>
          {loading ? "Uploading..." : "Upload PDF"}
        </button>
      </div>

      {notification && <p className="notification">{notification}</p>}

      <div className="question-section">
        {showQuestionBox && (
          <form onSubmit={handleAsk} className="question-form">
            <label>Ask a question about this PDF:</label>
            <textarea
              value={question}
              placeholder="Enter your question..."
              onChange={(e) => setQuestion(e.target.value)}
              rows={1}
              style={{
                minWidth: 300,
                maxWidth: "100%",
                width: "100%",
                minHeight: 40,
                maxHeight: 150,
                resize: "vertical"
              }}
            />
            <button type="submit" disabled={loading}>
              {loading ? "Asking..." : "Ask"}
            </button>
          </form>
        )}

        {answer && (
          <div className="answer-container" ref={answerRef}>
            <h3>Answer:</h3>
            <div className="answer-box">
              <pre>{answer}</pre>
            </div>
          </div>
        )}
      </div>

      <hr className="divider" />

      {/* ===== Global PDF Q&A Section ===== */}
      <div className="question-section global">
        <h1>Ask LLM anything across all stored PDFs</h1>

        {/* Document Type Buttons (BOTTOM) */}
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
          <textarea
            value={globalQuestion}
            placeholder="Enter your question..."
            onChange={(e) => setGlobalQuestion(e.target.value)}
            rows={1}
            style={{
              minWidth: 300,
              maxWidth: "100%",
              width: "100%",
              minHeight: 40,
              maxHeight: 150,
              resize: "vertical"
            }}
          />
          <button type="submit" disabled={globalLoading || !selectedTypeBottom}>
            {globalLoading ? "Searching..." : "Ask All"}
          </button>
        </form>

        {globalAnswer && (
          <div className="answer-container" ref={globalAnswerRef}>
            <h3>Global Answer:</h3>
            <div className="answer-box">
              <pre>{globalAnswer}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;