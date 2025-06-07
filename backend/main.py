from openai import OpenAI
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv
import os

# ===== S3 utility imports =====
from s3_utils import upload_fileobj_to_s3, download_file_from_s3, list_pdfs_in_s3

def get_temp_path(filename):
    temp_folder = os.path.join(os.getcwd(), "tmp")
    os.makedirs(temp_folder, exist_ok=True)
    return os.path.join(temp_folder, filename)

# ====== .env setup ======
dotenv_path = find_dotenv()
loaded = load_dotenv(dotenv_path, override=True)
print(f".env loaded: {loaded} from {dotenv_path}")
if not loaded:
    raise ValueError("Failed to load .env file! Make sure it exists and is properly formatted.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file!")
print("Loaded OpenAI Key:", OPENAI_API_KEY[:10] + "..." + OPENAI_API_KEY[-10:])  # masked

try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    models = client.models.list()
    print("API key is valid. Models available:", [m.id for m in models.data])
except Exception as e:
    print("API key error:", e)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTORSTORE_PATH = "vectorstore/faiss_index"
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# ====== Custom PromptTemplate for RetrievalQA ======
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

#=========================================================

@app.post("/upload-pdf/")
async def upload_pdf(pdf: UploadFile = File(...)):
    print("\n[UPLOAD] Starting PDF upload and indexing process...")
    pdf.file.seek(0)
    success = upload_fileobj_to_s3(pdf.file, pdf.filename)
    if not success:
        print("[UPLOAD] Upload to S3 failed!")
        return {"error": "Upload to S3 failed."}
    temp_path = get_temp_path(pdf.filename)
    download_success = download_file_from_s3(pdf.filename, temp_path)
    if not download_success:
        print("[UPLOAD] Download from S3 failed!")
        return {"error": "Failed to download uploaded PDF from S3 for indexing."}

    loader = PyPDFLoader(temp_path)
    docs = loader.load()
    print(f"[UPLOAD] Loaded {len(docs)} pages from '{pdf.filename}'")
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"[UPLOAD] Split into {len(chunks)} chunks. Sample: {chunks[0].page_content[:120] if chunks else 'NO CHUNKS'}")

    if os.path.exists(VECTORSTORE_PATH):
        print("[UPLOAD] Loading existing vectorstore and adding new docs...")
        vectorstore = FAISS.load_local(
            VECTORSTORE_PATH, embedding_model, allow_dangerous_deserialization=True
        )
        vectorstore.add_texts(
            [doc.page_content for doc in chunks],
            metadatas=[doc.metadata for doc in chunks]
        )
    else:
        print("[UPLOAD] Creating new vectorstore...")
        vectorstore = FAISS.from_documents(chunks, embedding_model)
    vectorstore.save_local(VECTORSTORE_PATH)
    print(f"[UPLOAD] Indexed: {pdf.filename}")

    if os.path.exists(temp_path):
        os.remove(temp_path)

    print("[UPLOAD] Done!\n")
    return {"message": "PDF uploaded and indexed successfully.", "filename": pdf.filename}

#=========================================================
@app.post("/ask-pdf/")
async def ask_pdf(question: str = Form(...), filename: str = Form(...)):
    try:
        print(f"\n[ASK-PDF] Received question for file: {filename}")
        temp_path = get_temp_path(filename)
        success = download_file_from_s3(filename, temp_path)
        if not success:
            print("[ASK-PDF] Download from S3 failed!")
            return {"answer": "Error downloading PDF from S3."}

        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        print(f"[ASK-PDF] Loaded {len(docs)} pages from '{filename}'")
        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = filename

        if chunks:
            print(f"[ASK-PDF] Sample chunk: {chunks[0].page_content[:150]}")
        else:
            print("[ASK-PDF] No chunks created from this PDF!")
            return {"answer": "PDF appears empty or unreadable."}

        vectorstore = FAISS.from_documents(chunks, embedding_model)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

        # DEBUG: Print context passed to LLM
        retrieved_docs = retriever.get_relevant_documents(question)
        print("[ASK-PDF] Retrieved docs:", [d.page_content[:200] for d in retrieved_docs])

        if not retrieved_docs or not any(d.page_content.strip() for d in retrieved_docs):
            print("[ASK-PDF] No content retrieved for this question.")
            return {"answer": "Not found in the document."}

        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4o",
            temperature=0,
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

        result = await run_in_threadpool(qa_chain, {"query": question})
        raw_answer = result['result'].strip()
        print("[ASK-PDF] Raw LLM answer:", raw_answer)
        print("[ASK-PDF] Sources used:", [doc.page_content[:200] for doc in result.get('source_documents', [])])

        # Post-process answer
        if not raw_answer or "not found" in raw_answer.lower():
            print("[ASK-PDF] Final answer returned: Not found in the document.")
            if retrieved_docs and any(d.page_content.strip() for d in retrieved_docs):
                context_snippet = retrieved_docs[0].page_content.strip()[:1000]
                answer = f"Direct answer not found. Here is the most relevant content from the document:\n\n{context_snippet}"
            else:
                answer = "Not found in the document."
        else:
            print("[ASK-PDF] Final answer returned:", raw_answer)
            answer = raw_answer

        if os.path.exists(temp_path):
            os.remove(temp_path)
        print("[ASK-PDF] Done!\n")
        return {"answer": answer}
    except Exception as e:
        print("Error in /ask-pdf:", e)
        return {"answer": f"Something went wrong while processing your PDF question: {str(e)}"}


#=========================================================
@app.post("/ask-all-pdfs/")
async def ask_all_pdfs(request: Request):
    try:
        print("\n[ASK-ALL] Starting multi-PDF global question process...")
        data = await request.json()
        question = data.get("question")
        if not question:
            print("[ASK-ALL] No question provided.")
            return {"answer": "No question provided."}

        pdf_filenames = list_pdfs_in_s3()
        print(f"[ASK-ALL] S3 PDFs found: {pdf_filenames}")
        if not pdf_filenames:
            return {"answer": "No PDF documents found in S3 bucket."}

        all_docs = []
        temp_paths = []
        for filename in pdf_filenames:
            temp_path = get_temp_path(filename)
            temp_paths.append(temp_path)
            success = download_file_from_s3(filename, temp_path)
            if not success:
                print(f"[ASK-ALL] Download failed for: {filename}")
                continue
            loader = PyPDFLoader(temp_path)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = filename
            all_docs.extend(docs)
            if docs:
                print(f"[ASK-ALL] {filename} - Page 1 sample: {docs[0].page_content[:180]}")
        print(f"[ASK-ALL] Total docs/pages loaded: {len(all_docs)}")
        if not all_docs:
            print("[ASK-ALL] No readable PDF documents found in S3 bucket.")
            return {"answer": "No readable PDF documents found in S3 bucket."}

        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(all_docs)
        print(f"[ASK-ALL] Total chunks for search: {len(chunks)}")

        # --- Filter for filename in question ---
        file_filter = None
        for fname in pdf_filenames:
            # fuzzy match (handle spaces, underscores, etc)
            if fname.lower().replace(".pdf", "").replace("_", " ").replace("-", " ") in question.lower().replace("_", " ").replace("-", " "):
                file_filter = fname
                break

        # NEW: Concatenate all chunks for file-matched questions
        if file_filter:
            print(f"[ASK-ALL] Filtering chunks for file: {file_filter}")
            filtered_chunks = [chunk for chunk in chunks if chunk.metadata.get("source") == file_filter]
            if not filtered_chunks:
                print("[ASK-ALL] No chunks found for that file!")
                return {"answer": f"No content found for {file_filter}."}
            from langchain.schema import Document
            combined_text = "\n\n".join([chunk.page_content for chunk in filtered_chunks])
            full_doc = Document(page_content=combined_text, metadata={"source": file_filter})
            chunks = [full_doc]  # just one big doc for the LLM to read

        if chunks:
            print(f"[ASK-ALL] Sample chunk: {chunks[0].page_content[:150]}")
        else:
            print("[ASK-ALL] No chunks created from any PDF!")
            return {"answer": "No readable content in any PDF."}

        vectorstore = FAISS.from_documents(chunks, embedding_model)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})  # More context for better answers

        # DEBUG: Print the context passed to LLM
        retrieved_docs = retriever.get_relevant_documents(question)
        print("[ASK-ALL] Retrieved docs for question:", [d.page_content[:200] for d in retrieved_docs])
        print("[ASK-ALL] Context for LLM:\n---\n", "\n\n".join([d.page_content for d in retrieved_docs]), "\n---\n")

        # Early return if nothing found
        if not retrieved_docs or not any(d.page_content.strip() for d in retrieved_docs):
            print("[ASK-ALL] No content retrieved for this question.")
            return {"answer": "Not found in the documents."}

        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4o",
            temperature=0,
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

        # Call the LLM chain
        result = await run_in_threadpool(qa_chain, {"query": question})
        raw_answer = result['result'].strip()
        print("[ASK-ALL] Raw LLM answer:", raw_answer)
        print("[ASK-ALL] Sources used:", [doc.page_content[:200] for doc in result.get('source_documents', [])])

        # Post-process answer
        if not raw_answer or "not found" in raw_answer.lower():
            print("[ASK-ALL] Final answer returned: Not found in the documents.")
            # Fallback: Show the most relevant context from the PDF
            if retrieved_docs and any(d.page_content.strip() for d in retrieved_docs):
                # Return the first (most relevant) chunk, truncated for brevity
                context_snippet = retrieved_docs[0].page_content.strip()[:1000]  # adjust length as desired
                answer = f"Direct answer not found. Here is the most relevant content from the document:\n\n{context_snippet}"
            else:
                answer = "Not found in the documents."
        else:
            print("[ASK-ALL] Final answer returned:", raw_answer)
            answer = raw_answer

        # Clean up
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
        print("[ASK-ALL] Done!\n")
        return {"answer": answer}
    except Exception as e:
        print("Error in /ask-all-pdfs:", e)
        return {"answer": f"Something went wrong while processing your global question: {str(e)}"}