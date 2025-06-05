from openai import OpenAI
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv, find_dotenv
import shutil
import os

# ===== Load from .env file =====
dotenv_path = find_dotenv()
loaded = load_dotenv(dotenv_path, override=True)
print(f".env loaded: {loaded} from {dotenv_path}")
if not loaded:
    raise ValueError("Failed to load .env file! Make sure it exists and is properly formatted.")

# ===== Load API Key from environment =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file!")
print("Loaded OpenAI Key:", OPENAI_API_KEY[:10] + "..." + OPENAI_API_KEY[-10:])  # masked

# ===== Validate API key =====
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    models = client.models.list()
    print("API key is valid. Models available:", [m.id for m in models.data])
except Exception as e:
    print("API key error:", e)

# ===== Initialize FastAPI app =====
app = FastAPI()

# ===== Enable CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Define paths and models =====
UPLOAD_FOLDER = "uploads"
VECTORSTORE_PATH = "vectorstore/faiss_index"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# ===== Route: Upload PDF and index into FAISS =====
@app.post("/upload-pdf/")
async def upload_pdf(pdf: UploadFile = File(...)):
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    if os.path.exists(VECTORSTORE_PATH):
        vectorstore = FAISS.load_local(VECTORSTORE_PATH, embedding_model)
        vectorstore.add_documents(chunks)
    else:
        vectorstore = FAISS.from_documents(chunks, embedding_model)

    vectorstore.save_local(VECTORSTORE_PATH)
    print(f"Indexed: {pdf.filename}")

    return {"message": "PDF uploaded and indexed successfully.", "filename": pdf.filename}

# ===== Route: Ask a question about a single uploaded PDF =====
@app.post("/ask-pdf/")
async def ask_pdf(question: str = Form(...), filename: str = Form(...)):
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)

    async def process_question():
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        if not docs:
            return {"answer": "PDF is empty or could not be read."}
        print(f"Loaded {len(docs)} pages")

        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        if not chunks:
            return {"answer": "Failed to process PDF content."}
        print(f"Split into {len(chunks)} chunks")

        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0)
        chain = load_qa_chain(llm, chain_type="stuff")

        if hasattr(chain, "ainvoke"):
            result = await chain.ainvoke({"input_documents": chunks, "question": question})
        else:
            result = await run_in_threadpool(chain.invoke, {"input_documents": chunks, "question": question})

        return {"answer": result.get("output_text", "No answer was generated.")}

    try:
        return await process_question()
    except Exception as e:
        print("Error in /ask-pdf:", e)
        return {"answer": f"Error processing your question: {str(e)}"}

# ===== Route: Ask a question across all PDFs using FAISS index =====
@app.post("/ask-all-pdfs/")
async def ask_all_pdfs(request: Request):
    try:
        data = await request.json()
        question = data.get("question")
        if not question:
            return {"answer": "No question provided."}

        if os.path.exists(VECTORSTORE_PATH):
            print("Loading existing FAISS vector store...")
            vectorstore = FAISS.load_local(VECTORSTORE_PATH, embedding_model)
        else:
            print("Creating new FAISS vector store...")
            all_docs = []
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.endswith(".pdf"):
                    path = os.path.join(UPLOAD_FOLDER, filename)
                    loader = PyPDFLoader(path)
                    docs = loader.load()
                    all_docs.extend(docs)

            if not all_docs:
                return {"answer": "No PDF documents found in uploads folder."}

            splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(all_docs)

            vectorstore = FAISS.from_documents(chunks, embedding_model)
            vectorstore.save_local(VECTORSTORE_PATH)

        # Perform similarity search
        top_k_docs = vectorstore.similarity_search(question, k=5)

        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0)
        chain = load_qa_chain(llm, chain_type="stuff")

        if hasattr(chain, "ainvoke"):
            result = await chain.ainvoke({"input_documents": top_k_docs, "question": question})
        else:
            result = await run_in_threadpool(chain.invoke, {"input_documents": top_k_docs, "question": question})

        return {"answer": result.get("output_text", "No answer was generated.")}

    except Exception as e:
        print("Error in /ask-all-pdfs:", e)
        return {"answer": f"Something went wrong while processing your global question: {str(e)}"}