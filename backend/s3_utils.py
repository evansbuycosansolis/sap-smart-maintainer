import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError

load_dotenv()  # Make sure your .env is loaded

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

def upload_fileobj_to_s3(fileobj, filename, bucket=AWS_S3_BUCKET):
    try:
        s3_client.upload_fileobj(fileobj, bucket, filename)
        return True
    except (BotoCoreError, ClientError) as e:
        print("S3 upload failed:", e)
        return False

def download_file_from_s3(filename, local_path, bucket=AWS_S3_BUCKET):
    try:
        with open(local_path, "wb") as f:
            s3_client.download_fileobj(bucket, filename, f)
        return True
    except (BotoCoreError, ClientError) as e:
        print("S3 download failed:", e)
        return False

def list_pdfs_in_s3(bucket=AWS_S3_BUCKET, prefix=""):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [item["Key"] for item in response.get("Contents", []) if item["Key"].endswith(".pdf")]
    except (BotoCoreError, ClientError) as e:
        print("S3 list failed:", e)
        return []