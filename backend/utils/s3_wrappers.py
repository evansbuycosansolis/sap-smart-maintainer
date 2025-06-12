from services.s3_service import download_file_from_s3, upload_pdf_to_s3, list_pdfs_in_s3
import os

def download_file_from_s3_folder(s3_key, local_path, bucket=None):
    """
    Download a file from S3 using its full key (folder/filename).
    """
    folder, filename = os.path.split(s3_key)
    return download_file_from_s3(filename, local_path, folder=folder, bucket=bucket)

def list_pdfs_in_s3_folder(folder, bucket=None):
    """
    List all PDFs in an S3 folder, passing through to the main S3 service.
    """
    return list_pdfs_in_s3(prefix=folder, bucket=bucket)
