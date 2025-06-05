import React, { useState } from "react";
import axios from "axios";
import "./App.css";

// This is a simple React app that allows users to upload a PDF file,
// ask questions about the content of the PDF, and receive answers from a backend service.
function App() {
  const [file, setFile] = useState(null);
  const [filename, setFilename] = useState("No file chosen");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [notification, setNotification] = useState("");
  const [showQuestionBox, setShowQuestionBox] = useState(false);

  // Function to handle PDF upload
  const handleUpload = async () => {
    if (!file) {
      alert("Please choose a PDF first.");
      return;
    }
    if (file.type !== "application/pdf") {
      alert("Please upload a valid PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("pdf", file);
    
    try {
      await axios.post("http://localhost:8080/upload-pdf/", formData);
      setNotification("PDF uploaded successfully! Now ask a question below.");
      setShowQuestionBox(true);
    } catch (error) {
      console.error("Upload error:", error);
      setNotification("Failed to upload PDF.");
    }
  };


  // Function to handle asking a question about the uploaded PDF
  // It sends the question and the filename to the backend service.
  // The backend service is expected to process the PDF and return an answer.
  // If the answer is a string, it is displayed directly; otherwise, it is stringified for display.
  // If an error occurs during the request, an error message is displayed.
  // The answer is displayed in a styled box below the question input.
  // The question input is only shown after a successful PDF upload.
  // The filename is displayed next to the file input, and the upload button is styled.
  // The app also includes basic error handling for file type and upload errors.
  // The app uses axios for HTTP requests and maintains state using React hooks.
  // The app is styled with a simple CSS file for better user experience.
  // The app is designed to run on a local server at http://localhost:8080.
  // The app is a frontend for a service that processes PDFs and answers questions about their content.
  // The app is built with React and uses functional components and hooks for state management.

  const handleAsk = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append("question", question);
    formData.append("filename", file.name);

    try {
      const res = await axios.post("http://localhost:8080/ask-pdf/", formData);

      if (typeof res.data.answer === "string") {
        setAnswer(res.data.answer);
      } else {
        // handle weird case if answer is still object (fallback)
        setAnswer(JSON.stringify(res.data.answer, null, 2));
      }
    } catch (error) {
      console.error("Ask error:", error);
      setAnswer("Something went wrong while processing your question.");
    }
  };

  
  // The main component renders the file upload section, question input, and answer display.
  // It includes an input for file selection, a button to upload the PDF,
  // and a form to ask questions about the uploaded PDF.
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
            setNotification("");
            setAnswer("");
            setShowQuestionBox(false);
          }}
        />
        <span className="filename">{filename}</span>
        <button className="upload-btn" onClick={handleUpload}>
          Upload PDF
        </button>
      </div>

      {notification && <p className="notification">{notification}</p>}

      <div className="question-section">
        {showQuestionBox && (
          <form onSubmit={handleAsk} className="question-form">
            <label>Ask a question about your PDF:</label>
            <input
              type="text"
              value={question}
              placeholder="Enter your question..."
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button type="submit">Ask</button>
          </form>
        )}

        {answer && (
          <div className="answer-container">
            <h3>Answer:</h3>
            <div className="answer-box">
              <p>{answer}</p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;