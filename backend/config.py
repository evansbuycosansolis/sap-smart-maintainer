# /backend/config.py

import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from services.s3_service import sanitize_s3_folder_name

dotenv_path = find_dotenv()
loaded = load_dotenv(dotenv_path, override=True)
if not loaded:
    raise ValueError("Failed to load .env file! Make sure it exists and is properly formatted.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file!")

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

VECTORSTORE_PATH = os.path.join("vectorstore", "faiss_index")
INDEXED_FILES_PATH = os.path.join("vectorstore", "indexed_files.pkl")

embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

qa_template = """
You are a helpful assistant. Use ONLY the context below to answer the user's question.
If the answer cannot be found directly, but you can summarize or infer from the context, please do so.
If the answer cannot be found at all, say "Not found in the documents."

Context:
{context}

Question: {question}

Answer:
"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=qa_template,
)

def setup_cors(app):
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
