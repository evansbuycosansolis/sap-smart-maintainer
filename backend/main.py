# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.pdf_routes import router as pdf_router
from services.s3_auto_index import auto_index_all_pdfs_in_s3
from fastapi.responses import JSONResponse
from status import indexing_status

app = FastAPI(
    title="SAP Smart Maintainer API",
    description="Backend API for PDF management and LLM integration",
    version="1.5.0"  # Update to match your actual release!
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # For production, use your frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "SAP Smart Maintainer backend is running."
    }

@app.get("/api/indexing-status/")
def get_indexing_status():
    """Get real-time status of S3 auto-indexing."""
    return JSONResponse(content=indexing_status)

@app.on_event("startup")
def startup_event():
    """Auto-index all S3 PDFs on server startup."""
    auto_index_all_pdfs_in_s3()

# Mount PDF API router under /api
app.include_router(pdf_router, prefix="/api")
