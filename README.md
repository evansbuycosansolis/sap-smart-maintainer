# SAP Smart Maintainer

**Version 1.3.0 – Vector Store Integration for Long-Term PDF Q&A**
SAP Smart Maintainer is a GenAI-powered assistant built to complement SAP Plant Maintenance (PM) systems by enabling intelligent, long-term PDF manual analysis.

---

## PDF Manual Q&A (v1.3.0)

- Upload SAP Plant Maintenance manuals in PDF format
- Ask questions in natural language
- **FAISS-based vector search** indexes all PDFs and retrieves the most relevant content
- Get fast and accurate answers using OpenAI GPT-4o via LangChain

---

## Tech Stack

- **Python FastAPI** – lightweight async backend
- **LangChain** – for LLM chaining, vector search, and document Q&A
- **OpenAI GPT-4o** – for intelligent response generation
- **FAISS** – for storing and retrieving relevant PDF chunks
- **PyPDFLoader** – to parse and chunk PDF documents
- **React.js** – frontend interface to upload and query PDFs

---

## Project Structure

sap-smart-maintainer/
├── backend/
│ ├── main.py # FastAPI app for PDF Q&A
│ ├── uploads/ # Uploaded PDF files
│ ├── vectorstore/ # FAISS index directory
│ ├── .env # (Not committed) OpenAI API key
│ └── requirements.txt # Python dependencies
├── frontend/
│ └── sap-frontend/ # React app for user interface
├── .gitignore
├── CHANGELOG.md
└── README.md

---

## How to Run Locally

### 1. Clone the Repo

git clone <https://github.com/evansbuycosansolis/sap-smart-maintainer.git>
cd sap-smart-maintainer

### 2. Setup the Backend

cd backend
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

Create a .env file in the backend/ directory:
OPENAI_API_KEY=sk-...your_openai_key_here...

### 3. Run the FastAPI Backend

uvicorn main:app --reload --port 8080

### 4. Run the Frontend (React)

cd ../frontend/sap-frontend
npm install
npm start

## Live Demo & Usage

Once running:
Go to <http://localhost:3000>
Upload your PDF manual
Ask a question about it
View the AI-generated answer
