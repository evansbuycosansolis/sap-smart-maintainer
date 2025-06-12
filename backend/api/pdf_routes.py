from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from services.pdf_service import (
    process_and_index_pdf,
    ask_pdf,
    ask_all_pdfs,
    reindex_all_pdfs,
)
from status import (
    get_indexing_status,
    update_indexing_status,  # For completeness, but you shouldn't need this here!
)

router = APIRouter()

@router.post("/api/upload-pdf/")
async def upload_pdf(
    pdf: UploadFile = File(...),
    category: str = Form(...)
):
    # All indexing logic/updates are handled within process_and_index_pdf
    ok, msg = await run_in_threadpool(process_and_index_pdf, pdf.file, pdf.filename, category)
    if ok:
        return {"message": msg, "filename": pdf.filename}
    return {"error": msg}

@router.post("/api/ask-pdf/")
async def ask_pdf_route(request: Request):
    data = await request.json()
    question = data.get("question")
    filename = data.get("filename")
    category = data.get("category")
    if not question or not filename or not category:
        return {"answer": "Missing required fields."}
    answer = await ask_pdf(question, filename, category)
    return {"answer": answer}

@router.post("/api/ask-all-pdfs/")
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
    # Use the getter so future implementations are thread-safe
    return get_indexing_status()

@router.post("/api/reindex-pdfs/")
async def reindex_pdfs_route():
    try:
        # All status update logic handled inside reindex_all_pdfs
        await run_in_threadpool(reindex_all_pdfs)
        return {"message": "Re-indexing started"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Re-indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
