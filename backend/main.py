from fastapi import FastAPI, UploadFile, File, Form
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import shutil
import os

app = FastAPI()
load_dotenv()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/ask-pdf/")
async def ask_pdf(question: str = Form(...), pdf: UploadFile = File(...)):
    # Save PDF
    pdf_path = f"{UPLOAD_FOLDER}/{pdf.filename}"
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    # Load PDF and split into chunks
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # LangChain QA
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    chain = load_qa_chain(llm, chain_type="stuff")
    answer = chain.invoke({"input_documents": chunks, "question": question})

    return {"answer": answer}
