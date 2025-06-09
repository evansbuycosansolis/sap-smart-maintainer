# backend/config.py

import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate

# If you want the sanitizer available everywhere, import it:
from services.s3_service import sanitize_s3_folder_name

# ======================================================================
# ====== .env and Key Loading ======
# ======================================================================
dotenv_path = find_dotenv()
loaded = load_dotenv(dotenv_path, override=True)
if not loaded:
    raise ValueError("Failed to load .env file! Make sure it exists and is properly formatted.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file!")

# S3 Configurations
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # default region

if not AWS_S3_BUCKET or not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS S3 credentials are not set in the .env file!")

# Debug: NEVER print keys in production!
#print("Loaded OpenAI Key: ************")  # Masked for safety

# ======================================================================
# ====== Constants and Paths ======
# ======================================================================
VECTORSTORE_PATH = os.path.join("vectorstore", "faiss_index")

# ======================================================================
# ====== Embedding Model (Global) ======
# ======================================================================
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# ======================================================================
# ====== Prompt Template ======
# ======================================================================
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

# ======================================================================
# ====== CORS Utility (OPTIONAL: usually in main.py) ======
# ======================================================================
def setup_cors(app):
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ======================================================================