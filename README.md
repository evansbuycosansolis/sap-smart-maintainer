# SAP Smart Maintainer

**What’s New in v1.6.0 (2025-06-12)

- FAISS Index Security. Uses allow_dangerous_deserialization=True when loading the FAISS index for trusted, locally created index files. Improved error messages for missing/corrupt indexes.
- AWS S3 Configuration & Robustness. Hardened .env loading and S3 variable checks. All S3 uploads/downloads/listings use sanitized, underscore-based names—no more surprises with spaces or symbols!
- UI/UX Enhancements.
  - Clear Buttons: Instantly clear Q&A boxes with one click.
  - Answer areas and PDF lists auto-clear on reset/upload.
  - More accurate “Indexing…” progress and notifications.
  - Answer display improved for code and long text.

---

## Added

Major Changes

- Auto-indexing Script: Automatically builds/updates the vectorstore from all S3 PDFs at server start.
- UI Polish: Animations, fade-in notifications, and mobile-friendly layout.
- User Feedback: Auto-scrolls to answers, instant upload/Q&A status.
- Manual Clear: Users can reset answers and file lists on demand.
- S3 Troubleshooting: Clearer bucket policy, public access, and permission guidance in logs and errors.
- Indexing Polling: Frontend now polls for indexing status only while indexing is active.
- Frontend Reset: All UI states and progress bars reset smoothly on new actions.
- Backend Refactor: Unified logging, cleaner services, and utilities.
- Vectorstore Loader: Safer, more robust FAISS loading from disk.
- Sanitization: File/folder names always normalized for S3 compatibility.

---

## Fixed

- Startup Failures: App won’t crash if index/S3 env missing—shows instructions instead.
- Bucket Name/Env Sensitivity: S3 env var issues fully resolved.
- Reindex Triggering: Button and indexing status now robust to S3 errors or concurrency.
- Progress Bar: No longer gets stuck or misaligned after clear/upload.
- Error States: Improved error handling everywhere

---

## How It Works

- PDF Upload: Users upload one or more SAP PM (or any) PDF files. Files are sanitized and stored in Amazon S3.
- Indexing: On startup (or manual reindex), the backend loads all PDFs from S3, splits them into chunks, embeds them, and stores the index locally with FAISS.
- Q&A:
  - Ask about a single PDF: Select a doc type, upload, and ask your question.
  - Ask across all PDFs: Select a doc type, ask, and get the best answer across your library.
- Instant Feedback: UI shows upload, indexing, and answer status with clear notifications and auto-scroll.
- Clear Answers: New "Clear" button resets Q&A fields instantly for a smoother workflow.

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

## Security Notes

- Only set allow_dangerous_deserialization=True for trusted, local FAISS indexes.

- Restrict CORS for production – update config.py with your domain!

- Make sure S3 bucket has correct public or IAM policy for access.

- Never store API keys in frontend/public code.

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
