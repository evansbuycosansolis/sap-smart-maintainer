from openai import OpenAI
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import shutil
import os

# ===== Load from .env file =====
dotenv_path = find_dotenv()
loaded = load_dotenv(dotenv_path)
print(f".env loaded: {loaded} from {dotenv_path}")
loaded = load_dotenv(dotenv_path, override=True)  # <-- Force override!
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


# ===== Ensure upload folder exists =====
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



# ===== Route: Upload PDF =====
@app.post("/upload-pdf/")
async def upload_pdf(pdf: UploadFile = File(...)):
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)
    print(f"Uploaded: {pdf_path}")
    return {"message": "PDF uploaded successfully.", "filename": pdf.filename}



# ===== Route: Ask a question about the uploaded PDF =====
@app.post("/ask-pdf/")
async def ask_pdf(question: str = Form(...), filename: str = Form(...)):
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        # Load and split PDF
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

        # Call OpenAI via LangChain
        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0)
        chain = load_qa_chain(llm, chain_type="stuff")
        result = chain.invoke({"input_documents": chunks, "question": question})
        print("Chain result:", result)

        return {"answer": result.get("output_text", "No answer was generated.")}

    except Exception as e:
        print("Error in /ask-pdf:", e)
        return {"answer": f"Error processing your question: {str(e)}"}