from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.concurrency import run_in_threadpool
from services.pdf_service import (
    process_and_index_pdf,
    ask_pdf,
    ask_all_pdfs,
)
from status import indexing_status


router = APIRouter()

@router.post("/upload-pdf/")
async def upload_pdf(
    pdf: UploadFile = File(...),
    category: str = Form(...)
):
    ok, msg = await run_in_threadpool(process_and_index_pdf, pdf.file, pdf.filename, category)
    if ok:
        return {"message": msg, "filename": pdf.filename}
    return {"error": msg}

@router.post("/ask-pdf/")
async def ask_pdf_route(request: Request):
    data = await request.json()
    question = data.get("question")
    filename = data.get("filename")
    category = data.get("category")
    if not question or not filename or not category:
        return {"answer": "Missing required field."}
    answer = await ask_pdf(question, filename, category)
    return {"answer": answer}

@router.post("/ask-all-pdfs/")
async def ask_all_pdfs_route(request: Request):
    data = await request.json()
    question = data.get("question")
    category = data.get("category")
    if not question:
        return {"answer": "No question provided."}
    answer = await ask_all_pdfs(question, category)
    return {"answer": answer}

@router.get("/api/indexing-status/")
def indexing_status_route():
    return indexing_status

