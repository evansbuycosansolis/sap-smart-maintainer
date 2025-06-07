import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
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

  const handleUpload = async () => {
    if (!file) return alert("Please choose a PDF first.");
    if (file.type !== "application/pdf") return alert("Please upload a valid PDF file.");

    const formData = new FormData();
    formData.append("pdf", file);

    try {
      setLoading(true);
      await axios.post("http://localhost:8080/upload-pdf/", formData);
      setNotification("PDF uploaded successfully! Now ask a question below.");
      setShowQuestionBox(true);
    } catch (error) {
      console.error("Upload error:", error);
      setNotification("Failed to upload PDF.");
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return alert("Enter a question.");

    const formData = new FormData();
    formData.append("question", question);
    formData.append("filename", file.name);

    try {
      setLoading(true);
      const res = await axios.post("http://localhost:8080/ask-pdf/", formData);
      setAnswer(typeof res.data.answer === "string" ? res.data.answer : JSON.stringify(res.data.answer, null, 2));
    } catch (error) {
      console.error("Ask error:", error);
      setAnswer("Something went wrong while processing your question.");
    } finally {
      setLoading(false);
    }
  };

  const handleAskAll = async (e) => {
    e.preventDefault();
    if (!globalQuestion.trim()) return alert("Enter a global question.");

    try {
      setGlobalLoading(true);
      const res = await axios.post("http://localhost:8080/ask-all-pdfs/", {
        question: globalQuestion,
      });
      setGlobalAnswer(res.data.answer || "No answer was generated.");
    } catch (error) {
      console.error("Global ask error:", error);
      setGlobalAnswer("Something went wrong while processing your global question.");
    } finally {
      setGlobalLoading(false);
    }
  };

  const resetUI = () => {
    setNotification("");
    setAnswer("");
    setShowQuestionBox(false);
  };

  return (
    <div className="container">
      <h1>Ask LLM about this PDF</h1>
      <div className="upload-section">
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
          <div className="answer-container">
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
          <button type="submit" disabled={globalLoading}>
            {globalLoading ? "Searching..." : "Ask All"}
          </button>
        </form>

        {globalAnswer && (
          <div className="answer-container">
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