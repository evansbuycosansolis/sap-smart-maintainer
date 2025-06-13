# Changelog

## [v1.1.0] – 2025-06-04

### Added

- Async and threadpool support using `asyncio.to_thread()` or `run_in_threadpool()`
- Switched to `ainvoke()` where supported for scalable LangChain execution

### Changed

- Refactored `ask_pdf()` route to support async processing
- Improved FastAPI compatibility for high-concurrency workloads

### Fixed

- `.env` loading logic to prevent accidental failures on reload
- Removed hardcoded API keys and ensured `.env` security

---

## [v1.0.0] – Initial Release

- Basic PDF Q&A system using LangChain and GPT-4o
- React frontend with upload + ask flow

## [1.2.0] - 2025-06-05

Added

- New global Q&A section that allows users to ask questions across **all stored PDFs**
- New `/ask-all-pdfs/` FastAPI route to handle multi-PDF document processing
- New React `globalQuestion` + `globalAnswer` UI section with scrollable output
- Design partition using `<hr />` for clear UI separation between single-PDF and all-PDF questions

Changed

- Refined frontend structure and styling
- Backend PDF loading uses batch file reading from `/uploads` directory

Fixed

- Better error handling for missing files and malformed questions

## [v1.3.0] - 2025-06-05

Added

- Integrated FAISS vector store to persistently index all uploaded PDFs for long-term use.
- Enabled top-k similarity search to retrieve only the most relevant document chunks.
- Automatically updates the vector index on every new PDF upload.
- Enhanced `/ask-all-pdfs/` endpoint to use vector-based retrieval instead of full document parsing.

Fixed

- Bug fix in `/ask-all-pdfs/`: added missing `question` extraction from JSON request body.

Dependencies

- Updated `requirements.txt` to include:
  - `faiss-cpu`
  - `langchain`
  - `langchain-openai`
  - `langchain-community`
  - `httpx`
  - `aiofiles`

Notes

- Improves scalability and performance for multi-document question answering.
- Prepares the backend for production-scale PDF storage and retrieval.

## [v1.4.0] – 2025-06-07

Major Changes

- **Switched Storage to Amazon S3:** All uploaded PDFs are now stored and loaded from Amazon S3, enabling scalable, cloud-based storage.
- **Global Q&A Improvements:** Multi-PDF question answering now provides more relevant content, even when an exact answer isn’t found.
- **Responsive UI:** Input and output containers grow vertically and are scrollable for large content, improving user experience on all devices.
- **Enhanced Context Matching:** Better fuzzy filename matching for more reliable PDF selection when asking questions across all PDFs.
- **Bug Fixes & Minor UI Tweaks:** Resolved issues with scrollbars and answer boxes.

Upgrade Notes

- You must configure your S3 credentials and bucket details in your `.env` file for uploads and retrieval to work.

## [v1.5.0] – 2025-06-08

Major Changes

- Pull S3 Document Workflow: All PDFs are uploaded, stored, and indexed from Amazon S3 for true scalability and cross-session access.
- Batch Auto-Indexing: On every server start, all S3 PDFs are batch-indexed for rapid search and reliable answers.
- Cleaner UI/UX.
  - Auto-scrolls to answer after each upload or question.
  - Improved progress bar logic—auto-resets on clear/upload, less redundant polling.
  - Smoother mobile experience, card layout, and animated notifications.
  - Accessibility improvements (keyboard focus, larger touch areas)

Added

- Auto-indexing script: New service automatically builds or updates vectorstore from all PDFs in S3.
- UI polish: Animations, notification fade-in, and responsive design.
- Feedback: Users get instant feedback after uploading or asking, with auto-scroll to answer.

Changed

- Polling Logic: Simplified frontend polling for indexing status—now only runs while indexing is active.
- Frontend Reset Logic: All UI state and progress bar now auto-clear on file change or reset.
- Backend Refactor:
  - Unified logging (replaced print with logger).
  - Service and utility modules cleaned up.

Fixed

- Progress Bar: No longer stuck or redundant after clear/upload.
- Category selection & error states: More robust error handling in frontend and backend.

Notes

- Make sure your .env file includes S3 and OpenAI keys.
- For production, always restrict CORS to your frontend domain.
- This version is ready for large-scale PDF libraries with cloud storage and fast search!

## [v1.6.0] – 2025-06-12

Major Changes

- FAISS Index Deserialization Security
  - Updated backend to use allow_dangerous_deserialization=True when loading FAISS index and doc metadata. This is now a documented requirement for LangChain/FAISS > 0.1.0, but only if you trust your pickle files (i.e., created by your own app).
  - Improved vectorstore loading error messages for missing or corrupt indexes.

- AWS S3 Configuration & Robustness
  - Hardened .env detection and S3 environment variable loading (e.g., AWS_S3_BUCKET), with clearer errors if unset.
  - Ensured all S3 uploads, downloads, and listings use standardized, sanitized file and folder names (spaces/special chars replaced with underscores).

- UI/UX Improvements
  - Added Clear button(s) for answer boxes (PDF and Global Q&A), allowing users to instantly reset Q&A output without refreshing the page.
  - Answer areas and file lists now auto-clear on new actions or resets.
  - Fine-tuned “Indexing…” status logic and notifications for even better feedback.
  - Enhanced answer display (better scroll, code-friendly font for output)..

Added

- Auto-indexing script: New service automatically builds or updates vectorstore from all PDFs in S3.
- UI polish: Animations, notification fade-in, and responsive design.
- Feedback: Users get instant feedback after uploading or asking, with auto-scroll to answer.
- Manual Clear Buttons
  - Users can now clear local/global answers with a single click.
- Bucket Policy/S3 Troubleshooting Documentation
  - Added more helpful error messages and documentation for AWS S3 public access, permissions, and bucket policy configuration steps.

Changed

- Polling Logic: Simplified frontend polling for indexing status—now only runs while indexing is active.
- Frontend Reset Logic: All UI state and progress bar now auto-clear on file change or reset.
- Backend Refactor:
  - Unified logging (replaced print with logger).
  - Service and utility modules cleaned up.
- Vectorstore Loader. Loading from local disk now always uses the correct pickle option, prevents common startup errors.
- Backend Logging. More informative S3 and FAISS log output (shows config/permission errors, what’s indexed, etc).
- Sanitization. Further enforced consistent S3 key naming conventions for cross-platform compatibility.

Fixed

- Critical App-Startup Failures. App no longer crashes if FAISS index is missing or S3 environment variables aren’t set—provides clear instructions instead.
- Bucket Name/Env Case Sensitivity. Resolved issues where S3 env vars were set but not detected due to naming mismatches.
- Re-index Triggering. Fixed issues with reindex button when indexing already running or S3 misconfigured.Progress Bar: No longer stuck or redundant after clear/upload.
- Category selection & error states: More robust error handling in frontend and backend.

Notes

- Make sure your .env file includes S3 and OpenAI keys.
- For production, always restrict CORS to your frontend domain.
- This version is ready for large-scale PDF libraries with cloud storage and fast search!


## [v1.7.0] – 2025-06-13

### Major Changes

#### Predictive Analysis Engine
- Integrated asset health predictive workflow (LLM-powered) for equipment logs.
- Added support for custom analysis questions and sensor log upload.
- Summarizes risk, predicts failures, and outputs actionable recommendations from uploaded logs.

#### Voice Input/Output (Speech Synthesis)
- Added TTS (text-to-speech) voice output for predictive summaries and Q&A answers.
- Added voice input support (speech recognition) for Q&A, predictive questions, and search—works across PDF and global ask.
- Added “Stop All” button and automatic voice-cancel logic to prevent repeated or unwanted speech on app load or when switching tasks.

#### Auto-load & Auto-speak Enhancements
- Predictive summary now auto-loads and reads result aloud after analysis is complete.
- Added guards to prevent TTS from speaking empty or default “No” responses.
- Fixed bug where TTS would repeat or trigger on app load due to default/empty state.

#### Scrollable Context & Summary UI
- Predictive and context result boxes are now scrollable (with dark theme styling).
- Improved rendering of asset maintenance context and JSON outputs—better for long or complex responses.

---

### Added

- **Predictive Analysis Panel**
  - New UI box for predictive questions, log upload, and summary display.
  - “Ask” button for running custom LLM analysis queries.
  - Real-time display of risk, predicted failure, recommendation, and action fields.
- **Voice Experience**
  - Added automatic TTS output for all answer types (predictive, PDF Q&A, global Q&A).
  - Added visual voice mode toggle and feedback indicator (GIF/animation when active).
- **Scrollable Containers**
  - Scrollbars for asset context lists and raw JSON output, ensuring layout never overflows.

---

### Changed

- **Speech Synthesis/Recognition Logic**
  - Improved guards to block unwanted TTS on empty/default state.
  - Speech is now only triggered after valid analysis results (not on “No”/empty).
  - Defensive programming added to prevent “No” from being read repeatedly.
- **UX/Notifications**
  - Fine-tuned notifications and progress bars for clearer feedback during predictive, indexing, and upload tasks.
  - Auto-scroll to answers after Q&A, predictive analysis, or file upload.
- **Backend Predictive Analysis API**
  - Accepts analysis question and log text from user input (query box and upload).
  - Returns structured output with ML predictions and recommendations.

---

### Fixed

- **Voice “No” Spam**
  - Fixed bug causing multiple “No” outputs on app load or empty answer.
  - Resolved repeated TTS activation on state changes or re-render.
- **Overflow UI/UX**
  - Fixed predictive/context/JSON boxes overflowing parent containers.
  - Responsive adjustments for mobile and desktop.
- **Speech Synthesis Cancel**
  - `stopAll()` logic now runs at app load, on route changes, and before new voice output.
- **TTS/Recognition State**
  - Fixed issues where voice recognition or synthesis would continue running in background.

---

### Notes

- All predictive analysis features require a valid API backend with LLM + ML workflow.
- To avoid repeated “No” voice output, ensure that result and summary fields are never set to “No” by default; use `null` or `""` instead.
- For best results, keep `.env` and AWS/OpenAI keys up to date.
