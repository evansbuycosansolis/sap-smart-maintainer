# SAP Smart Maintainer

## Version 1.0.0 – PDF Q&A Reader

SAP Smart Maintainer is a GenAI-powered assistant built to complement SAP Plant Maintenance (PM) systems.

---

## PDF Manual Q&A (v1.0.0)

- Upload SAP Plant Maintenance manuals in PDF format
- Ask questions in natural language
- Get AI-generated answers using OpenAI GPT-4o via LangChain

---

## Tech Stack

- **Python FastAPI** – lightweight async backend
- **LangChain** – for LLM chaining and document Q&A
- **OpenAI GPT-4o** – for intelligent response generation
- **PyPDFLoader** – to parse and split PDF documents

## Project Structure

sap-smart-maintainer/
├── backend/
│ ├── main.py # FastAPI app for PDF Q&A
│ ├── uploads/ # Uploaded PDF files
│ └── requirements.txt
├── .gitignore
└── README.md

## How to Run Locally

1. Clone the repo:
git clone [https://github.com/evansbuycosansolis/sap-smart-maintainer.git]
