# backend/services/s3_service.py

import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError
import re
import logging
logger = logging.getLogger(__name__)

# ======================================================================
# Load env vars
# ======================================================================
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# ======================================================================
# S3 client singleton
# ======================================================================
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# ======================================================================
# Helper: Clean/Sanitize Folder and File Name for S3
# ======================================================================
def sanitize_s3_name(name):
    safe = re.sub(r"[^A-Za-z0-9_\-(). ]", "", name)
    safe = re.sub(r"\s+", " ", safe)
    safe = safe.strip().replace(" ", "_")
    return safe

sanitize_s3_folder_name = sanitize_s3_name  # For imports elsewhere

# ======================================================================
# Upload File to S3 (with Folder/Prefix)
# ======================================================================
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

# ======================================================================
# Download File from S3 (with Folder/Prefix)
# ======================================================================
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

# ======================================================================
# List PDF Files in S3 (optionally under sanitized prefix/folder)
# ======================================================================
def list_pdfs_in_s3(bucket=AWS_S3_BUCKET, prefix=""):
    try:
        sanitized_prefix = sanitize_s3_name(prefix) + "/" if prefix else ""
        logger.info(f"[S3 LIST] Listing PDFs under prefix: {sanitized_prefix}")
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=sanitized_prefix)
        logger.debug(f"[DEBUG] Raw prefix: '{prefix}' | Sanitized prefix: '{sanitized_prefix}'")
        return [
            os.path.basename(item["Key"])
            for item in response.get("Contents", [])
            if item["Key"].lower().endswith(".pdf")
        ]

    except (BotoCoreError, ClientError) as e:
        logger.error("S3 list failed: %s", e)
        return []

# ======================================================================
# Helper Wrappers for S3 "folder/filename" keys (optional, always sanitize)
# ======================================================================
def upload_fileobj_to_s3_folder(fileobj, s3_key, bucket=AWS_S3_BUCKET):
    folder, filename = os.path.split(s3_key)
    return upload_pdf_to_s3(fileobj, filename, folder=folder, bucket=bucket)

def download_file_from_s3_folder(s3_key, local_path, bucket=AWS_S3_BUCKET):
    folder, filename = os.path.split(s3_key)
    return download_file_from_s3(filename, local_path, folder=folder, bucket=bucket)

def list_pdfs_in_s3_folder(folder, bucket=AWS_S3_BUCKET):
    return list_pdfs_in_s3(bucket=bucket, prefix=folder)
