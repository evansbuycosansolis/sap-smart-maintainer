import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError
import re
import logging

from status import (
    update_indexing_status,
    reset_indexing_status,
    set_indexing_current_file,
    set_indexing_error,
    finish_indexing,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

def sanitize_s3_name(name):
    safe = re.sub(r"[^A-Za-z0-9_\-(). ]", "", name)
    safe = re.sub(r"\s+", " ", safe)
    safe = safe.strip().replace(" ", "_")
    return safe

sanitize_s3_folder_name = sanitize_s3_name

def list_pdfs_in_s3(bucket=AWS_S3_BUCKET, prefix=""):
    if not bucket:
        logger.error("AWS_S3_BUCKET is not set! Cannot list PDFs.")
        return []
    try:
        sanitized_prefix = sanitize_s3_name(prefix) + "/" if prefix else ""
        logger.info(f"[S3 LIST] Listing PDFs under prefix: {sanitized_prefix}")
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=sanitized_prefix)
        return [
            os.path.basename(item["Key"])
            for item in response.get("Contents", [])
            if item["Key"].lower().endswith(".pdf")
        ]
    except (BotoCoreError, ClientError) as e:
        logger.error("S3 list failed: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected S3 list error: %s", e)
        return []

def list_pdfs_in_s3_folder(folder, bucket=AWS_S3_BUCKET):
    return list_pdfs_in_s3(bucket=bucket, prefix=folder)

def download_file_from_s3(filename, local_path, folder=None, bucket=AWS_S3_BUCKET):
    try:
        sanitized_filename = sanitize_s3_name(filename)
        sanitized_folder = sanitize_s3_name(folder) if folder else ""
        s3_key = f"{sanitized_folder}/{sanitized_filename}" if sanitized_folder else sanitized_filename

        logger.info(f"[S3 DOWNLOAD] Downloading from: {bucket}/{s3_key}")
        with open(local_path, "wb") as f:
            s3_client.download_fileobj(bucket, s3_key, f)
        return True
    except (BotoCoreError, ClientError) as e:
        logger.error("S3 download failed: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected S3 download error: %s", e)
        return False

def download_file_from_s3_folder(s3_key, local_path, bucket=AWS_S3_BUCKET):
    folder, filename = os.path.split(s3_key)
    return download_file_from_s3(filename, local_path, folder=folder, bucket=bucket)

def upload_pdf_to_s3(fileobj, filename, folder=None, bucket=AWS_S3_BUCKET):
    try:
        sanitized_filename = sanitize_s3_name(filename)
        sanitized_folder = sanitize_s3_name(folder) if folder else ""
        s3_key = f"{sanitized_folder}/{sanitized_filename}" if sanitized_folder else sanitized_filename

        logger.info(f"[S3 UPLOAD] Uploading to: {bucket}/{s3_key}")
        s3_client.upload_fileobj(fileobj, bucket, s3_key)
        s3_url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"
        return s3_url
    except (BotoCoreError, ClientError) as e:
        logger.error("S3 upload failed: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected S3 upload error: %s", e)
        return None

async def download_all_pdfs_from_s3(local_dir):
    """
    Download all PDFs from all S3 folders to a local directory.
    This function is async-safe: it uses asyncio.to_thread for blocking S3 operations.
    Also updates indexing status.
    """
    import asyncio
    os.makedirs(local_dir, exist_ok=True)
    folders = [
        "Document_Management_System_(DMS)_Integration",
        "Maintenance_Notification_Documents",
        "Maintenance_Planning_Documents",
        "Procurement_and_Material_Management",
        "Reporting_and_Historical_Documents",
        "Work_Order_Documents",
    ]

    reset_indexing_status()
    total_files = 0
    for folder in folders:
        pdfs = list_pdfs_in_s3_folder(folder)
        total_files += len(pdfs)
    update_indexing_status(total=total_files, current=0, running=True)
    current_counter = 0

    for folder in folders:
        pdfs = list_pdfs_in_s3_folder(folder)
        for pdf in pdfs:
            local_path = os.path.join(local_dir, pdf)
            set_indexing_current_file(f"{folder}/{pdf}")
            if not os.path.exists(local_path):
                logger.info(f"[S3 → LOCAL] Downloading {folder}/{pdf} to {local_path}")
                try:
                    await asyncio.to_thread(download_file_from_s3, pdf, local_path, folder=folder)
                    current_counter += 1
                    update_indexing_status(current=current_counter)
                except Exception as e:
                    logger.error(f"Failed to download {folder}/{pdf}: {e}")
                    set_indexing_error(str(e))
            else:
                logger.info(f"[S3 → LOCAL] Exists: {local_path}, skipping.")
    finish_indexing()

__all__ = [
    "upload_pdf_to_s3",
    "download_file_from_s3",
    "list_pdfs_in_s3",
    "list_pdfs_in_s3_folder",
    "download_file_from_s3_folder",
    "sanitize_s3_folder_name",
    "download_all_pdfs_from_s3"
]
