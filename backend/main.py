# /backend/main.py

import os
from fastapi import FastAPI
from api.pdf_routes import router as pdf_router
from config import setup_cors
from services.s3_service import download_all_pdfs_from_s3
from services.vectorstore_manager import load_faiss_index
from api.rec_routes import router as rec_router  # <-- your new router
from api.predictive_routes import router as predictive_router


PDF_UPLOAD_DIR = "uploads"

app = FastAPI()  # <-- Define your app FIRST

setup_cors(app)
app.include_router(pdf_router)
app.include_router(rec_router)  
app.include_router(predictive_router)



@app.on_event("startup")
async def startup_event():
    # Step 1: Ensure upload dir exists
    os.makedirs(PDF_UPLOAD_DIR, exist_ok=True)
    print(f"[STARTUP] Upload directory: {os.path.abspath(PDF_UPLOAD_DIR)}")

    pdfs = [
        f for f in os.listdir(PDF_UPLOAD_DIR)
        if f.lower().endswith(".pdf")
        and os.path.isfile(os.path.join(PDF_UPLOAD_DIR, f))
        and not f.startswith('.')
    ]
    if not pdfs:
        print("[STARTUP] No PDFs found locally. Downloading from S3...")
        await download_all_pdfs_from_s3(PDF_UPLOAD_DIR)
    else:
        print(f"[STARTUP] Found {len(pdfs)} PDFs locally. Skipping S3 download.")

    # Step 2: Load FAISS index if present
    loaded = load_faiss_index()
    if loaded:
        print("[STARTUP] FAISS index loaded for queries.")
    else:
        print("[STARTUP] No FAISS index found. Please re-index or upload PDFs.")


