# SAP Smart Maintainer

**Version 1.5.0 – S3 Storage, UI/UX Polish, Auto-Indexing

- Amazon S3 Storage: All uploaded PDFs are stored and loaded from Amazon S3 for true scalability.
- Smarter Q&A: AI gives you relevant content—even if no exact answer exists—from the most appropriate document.
- Batch Auto-Indexing: On server start, all S3 PDFs are indexed for fast search.
- Cleaner & Responsive UI: Seamless mobile/desktop support, auto-scrolling to answers, and animated feedback.
- Fuzzy Filename Matching: Recognizes and matches PDF names within your questions for accurate retrieval.
- Bug Fixes & Reliability: Progress bar auto-resets, error handling improved, and overall app is more robust..

---

## PDF Manual Q&A (v1.4.0)

- Upload SAP Plant Maintenance manuals (PDF) — now stored in Amazon S3
- Ask questions in natural language about single or all PDFs
- FAISS-based vector search indexes all PDFs and retrieves the most relevant content
- Powered by OpenAI GPT-4o & LangChain for contextual answers
- If no direct answer is found, you’ll still get the most relevant content.

---

## Tech Stack

- Python FastAPI – Lightweight async backend
- LangChain – LLM Q&A, vector search, document parsing
- OpenAI GPT-4o – Intelligent, context-based answers
- FAISS – Efficient PDF chunk indexing and retrieval
- Amazon S3 – Cloud storage for all PDFs
- PyPDFLoader – PDF parsing/chunking
- React.js – Responsive user interfac

---

## Project Structure

sap-smart-maintainer/
├── backend/
│   ├── main.py             # FastAPI app for PDF Q&A
│   ├── api/                # API routes
│   ├── services/           # S3, PDF, vector utilities
│   ├── vectorstore/        # FAISS index directory
│   ├── .env                # (Not committed) API & S3 keys
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── sap-frontend/       # React app for user interface
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

- OPENAI_API_KEY=sk-...your_openai_key_here...
- AWS_ACCESS_KEY_ID=your_aws_access_key_id
- AWS_SECRET_ACCESS_KEY=your_aws_secret_key
- S3_BUCKET_NAME=your_s3_bucket_name


### 3. Run the FastAPI Backend

uvicorn main:app --reload --port 8080

### 4. Run the Frontend (React)

cd ../frontend/sap-frontend
npm install
npm start

## Live Demo & Usage

Once running:

- Go to <http://localhost:3000>
- Upload your PDF manual (now saved in Amazon S3)
- Ask a question about it or across all PDFs
- View the AI-generated answer or relevant document content
