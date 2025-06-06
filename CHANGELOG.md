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
