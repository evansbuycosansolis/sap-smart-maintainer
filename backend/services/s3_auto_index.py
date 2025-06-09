# backend/services/s3_auto_index.py

import os
import logging
from services.s3_service import list_pdfs_in_s3, download_file_from_s3, sanitize_s3_folder_name
from services.pdf_service import get_temp_path, process_and_index_pdf
from status import indexing_status

logger = logging.getLogger(__name__)

def auto_index_all_pdfs_in_s3():
    categories = [
        "Maintenance Notification Documents",
        "Costing and Controlling Documents",
        "Maintenance Planning Documents",
        "Reporting & Historical Documents",
        "Work Order Documents",
        "Authorizations and Change Logs",
        "Procurement & Material Management",
        "Document Management System (DMS) Integration"
    ]

    # Build list of all (category, pdf_filename) pairs
    pdf_list = []
    for category in categories:
        sanitized_category = sanitize_s3_folder_name(category)
        pdfs = list_pdfs_in_s3(prefix=sanitized_category)
        for pdf_filename in pdfs:
            pdf_list.append((category, pdf_filename))

    indexing_status["total"] = len(pdf_list)
    indexing_status["current"] = 0
    indexing_status["running"] = True

    for i, (category, pdf_filename) in enumerate(pdf_list, start=1):
        sanitized_category = sanitize_s3_folder_name(category)
        temp_path = get_temp_path(pdf_filename)
        ok = download_file_from_s3(pdf_filename, temp_path, folder=sanitized_category)
        if not ok:
            logger.warning(f"[AUTO-INDEX] Failed to download: {sanitized_category}/{pdf_filename}")
            continue

        logger.info(f"[AUTO-INDEX] Indexing: {sanitized_category}/{pdf_filename}")
        try:
            with open(temp_path, "rb") as f:
                process_and_index_pdf(f, pdf_filename, category, skip_s3_upload=True)
        except Exception as e:
            logger.error(f"[AUTO-INDEX] Exception indexing {pdf_filename}: {e}")
        finally:
            indexing_status["current"] = i
            if os.path.exists(temp_path):
                os.remove(temp_path)

    indexing_status["running"] = False
    indexing_status["current"] = indexing_status["total"]

