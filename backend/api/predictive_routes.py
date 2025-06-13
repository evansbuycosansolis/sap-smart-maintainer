from fastapi import APIRouter, UploadFile, File, Form
from services.s3_service import upload_pdf_to_s3
from services.langgraph_predictive import run_predictive_workflow
from utils.pdf_parser import parse_pdf_to_text
import os

router = APIRouter()

@router.post("/api/predictive-analyze/")
async def predictive_analyze(pdf: UploadFile = File(...), question: str = Form(None)):
    PREDICTIVE_ANALYTICS_FOLDER = "Asset_PredictiveAnalytics"

    # Save PDF to temp
    temp_path = f"./tmp/{pdf.filename}"
    with open(temp_path, "wb") as f:
        f.write(await pdf.read())

    # Upload to S3 (hardcoded folder)
    with open(temp_path, "rb") as f:
        upload_pdf_to_s3(f, pdf.filename, folder=PREDICTIVE_ANALYTICS_FOLDER)

    # Parse PDF and run LangGraph workflow
    sensor_log_text = parse_pdf_to_text(temp_path)
    result = run_predictive_workflow(sensor_log_text, question)

    # Clean up
    os.remove(temp_path)
    return result
