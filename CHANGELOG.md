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
