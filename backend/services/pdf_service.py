# /backend/services/pdf_service.py

import re
import os
from dotenv import load_dotenv
from fastapi.concurrency import run_in_threadpool
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema import Document

from services.vectorstore_manager import get_faiss_index, save_faiss_index, get_docs
from status import (
    update_indexing_status,
    reset_indexing_status,
    increment_indexing_current,
    set_indexing_current_file,
    set_indexing_error,
    finish_indexing,
    indexing_status
)
from config import VECTORSTORE_PATH, embedding_model, OPENAI_API_KEY
from services.s3_service import (
    upload_pdf_to_s3,
    download_file_from_s3,
    list_pdfs_in_s3,
    sanitize_s3_folder_name,
)
from utils.s3_wrappers import (
    list_pdfs_in_s3_folder,
    download_file_from_s3_folder,
)

def get_temp_path(filename):
    temp_folder = os.path.join(os.getcwd(), "tmp")
    os.makedirs(temp_folder, exist_ok=True)
    return os.path.join(temp_folder, filename)

S3_FOLDERS = [
    "Document_Management_System_(DMS)_Integration",
    "Maintenance_Notification_Documents",
    "Maintenance_Planning_Documents",
    "Procurement_and_Material_Management",
    "Reporting_and_Historical_Documents",
    "Work_Order_Documents",
]

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

TMP_DIR = "./tmp"
os.makedirs(TMP_DIR, exist_ok=True)






# ======= REINDEX ALL PDFS ==========
import re

def reindex_all_pdfs():
    print("[INFO] Starting full re-indexing of all S3 PDFs")
    reset_indexing_status()
    all_docs = []
    current_counter = 0
    for folder in S3_FOLDERS:
        filenames = [f for f in list_pdfs_in_s3_folder(folder) if f and isinstance(f, str)]
        print(f"[INFO] Indexing {folder}: {len(filenames)} PDFs")
        for filename in filenames:
            if not isinstance(filename, str) or not filename.strip() or not folder:
                print(f"[WARN] Invalid filename or folder: {folder}/{filename}")
                continue
            current_counter += 1
            update_indexing_status(current=current_counter, status=f"Indexing {folder}/{filename} ({current_counter})")
            set_indexing_current_file(f"{folder}/{filename}")
            local_path = os.path.join(TMP_DIR, filename)
            success = download_file_from_s3_folder(filename, local_path, folder=folder)
            if not success:
                print(f"[WARN] Skipped {filename} — download failed.")
                set_indexing_error(f"Failed to download {filename} from {folder}")
                continue
            try:
                loader = PyPDFLoader(local_path)
                raw_pages = loader.load()
                if not raw_pages:
                    print(f"[WARN] Empty PDF: {filename}")
                    continue
                splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = splitter.split_documents(raw_pages)

                # ========== ENRICH METADATA FOR EACH CHUNK ==========
                for chunk in chunks:
                    chunk.metadata["source"] = filename

                    # Equipment/Asset ID
                    match = re.search(r"(Equipment|Asset)[\s:]+([\w\-]+)", chunk.page_content)
                    if match:
                        chunk.metadata["asset_id"] = match.group(2)

                    # Failure Type
                    match = re.search(r"Failure Type[\s:]+([A-Za-z\s]+)", chunk.page_content)
                    if match:
                        chunk.metadata["failure_type"] = match.group(1).strip()

                    # Date
                    match = re.search(r"Date[\s:]+(\d{4}-\d{2}-\d{2})", chunk.page_content)
                    if match:
                        chunk.metadata["date"] = match.group(1)

                    # Handled By
                    match = re.search(r"Handled By[\s:]+([A-Za-z\s.]+)", chunk.page_content)
                    if match:
                        chunk.metadata["handled_by"] = match.group(1).strip()
                # ========== END METADATA ENRICHMENT ==========

                all_docs.extend(chunks)
            except Exception as e:
                print(f"[ERROR] Failed to process {filename}: {e}")
                set_indexing_error(str(e))
            finally:
                try:
                    os.remove(local_path)
                except Exception as e:
                    print(f"[WARN] Could not delete temp file: {e}")

    if all_docs:
        print(f"[INFO] Total chunks generated: {len(all_docs)}")
        from langchain_community.vectorstores import FAISS
        faiss_index = FAISS.from_documents(all_docs, embedding_model)
        save_faiss_index(faiss_index, all_docs)
        print("[INFO] Re-indexing completed and saved.")
    else:
        print("[WARN] No documents were indexed.")
    finish_indexing()








def process_and_index_pdf(pdf_file, pdf_filename, category=None, skip_s3_upload=False):
    sanitized_category = sanitize_s3_folder_name(category) if category else None

    # Upload to S3 if required
    if not skip_s3_upload:
        pdf_file.seek(0)
        upload_success = upload_pdf_to_s3(pdf_file, pdf_filename, folder=sanitized_category)
        if not upload_success:
            set_indexing_error("Upload to S3 failed.")
            return False, "Upload to S3 failed."

    temp_path = get_temp_path(pdf_filename)
    download_success = download_file_from_s3(pdf_filename, temp_path, folder=sanitized_category)
    if not download_success:
        set_indexing_error("Failed to download PDF from S3 for indexing.")
        return False, "Failed to download PDF from S3 for indexing."

    loader = PyPDFLoader(temp_path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # ===============================
    # Enrich metadata for each chunk
    # ===============================
    for chunk in chunks:
        chunk.metadata["source"] = pdf_filename

        # Extract Asset/Equipment ID
        match = re.search(r"(Equipment|Asset)[\s:]+([\w\-]+)", chunk.page_content)
        if match:
            chunk.metadata["asset_id"] = match.group(2)

        # Extract Failure Type
        match = re.search(r"Failure Type[\s:]+([A-Za-z\s]+)", chunk.page_content)
        if match:
            chunk.metadata["failure_type"] = match.group(1).strip()

        # Extract Date
        match = re.search(r"Date[\s:]+(\d{4}-\d{2}-\d{2})", chunk.page_content)
        if match:
            chunk.metadata["date"] = match.group(1)

        # Extract Handled By
        match = re.search(r"Handled By[\s:]+([A-Za-z\s.]+)", chunk.page_content)
        if match:
            chunk.metadata["handled_by"] = match.group(1).strip()

    # ===============================
    # Add to vectorstore and save
    # ===============================
    vectorstore = get_faiss_index()
    if vectorstore:
        vectorstore.add_texts([doc.page_content for doc in chunks], metadatas=[doc.metadata for doc in chunks])
        save_faiss_index(vectorstore, get_docs() + chunks)
    else:
        from langchain_community.vectorstores import FAISS
        vectorstore = FAISS.from_documents(chunks, embedding_model)
        save_faiss_index(vectorstore, chunks)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    finish_indexing()
    return True, "PDF indexed successfully." if skip_s3_upload else "PDF uploaded and indexed successfully."






import re

# ======= SINGLE PDF QUERY ==========
async def ask_pdf(question, filename, category=None):
    """
    Answer a question for a single PDF (optionally specifying a sanitized category/folder).
    """
    temp_path = get_temp_path(filename)
    sanitized_category = sanitize_s3_folder_name(category) if category else None

    try:
        # Download PDF from S3
        download_success = download_file_from_s3(filename, temp_path, folder=sanitized_category)
        if not download_success:
            return "Error downloading PDF from S3."

        # Load and split PDF
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        if not chunks:
            return "PDF appears empty or unreadable."

        # Enrich chunk metadata
        for chunk in chunks:
            chunk.metadata["source"] = filename

            # Regex-based metadata enrichment
            match = re.search(r"(Equipment|Asset)[\s:]+([\w\-]+)", chunk.page_content)
            if match:
                chunk.metadata["asset_id"] = match.group(2)

            match = re.search(r"Failure Type[\s:]+([A-Za-z\s]+)", chunk.page_content)
            if match:
                chunk.metadata["failure_type"] = match.group(1).strip()

            match = re.search(r"Date[\s:]+(\d{4}-\d{2}-\d{2})", chunk.page_content)
            if match:
                chunk.metadata["date"] = match.group(1)

            match = re.search(r"Handled By[\s:]+([A-Za-z\s.]+)", chunk.page_content)
            if match:
                chunk.metadata["handled_by"] = match.group(1).strip()

        # Create temporary vectorstore and retriever
        from langchain_community.vectorstores import FAISS
        vectorstore = FAISS.from_documents(chunks, embedding_model)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
        retrieved_docs = retriever.get_relevant_documents(question)

        if not retrieved_docs or not any(d.page_content.strip() for d in retrieved_docs):
            return "Not found in the document."

        # LLM Q&A
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

        if not raw_answer or "not found" in raw_answer.lower():
            if retrieved_docs and any(d.page_content.strip() for d in retrieved_docs):
                context_snippet = retrieved_docs[0].page_content.strip()[:1000]
                return f"Direct answer not found. Here is the most relevant content from the document:\n\n{context_snippet}"
            else:
                return "Not found in the document."
        return raw_answer

    finally:
        # Always clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"[WARN] Could not delete temp file: {e}")










# ======= GLOBAL QUERY (ALL INDEXED PDFS) ==========
async def ask_all_pdfs(question, category=None):
    """
    Answer a question across all PDFs (optionally restricted to a sanitized category/folder).
    Uses only the in-memory singleton FAISS index for fast querying.
    """
    vectorstore = get_faiss_index()
    if not vectorstore:
        return "No FAISS index loaded. Please re-index or upload PDFs first."
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

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


    if not raw_answer or "not found" in raw_answer.lower():
        docs = retriever.get_relevant_documents(question)
        if docs and any(d.page_content.strip() for d in docs):
            context_snippet = docs[0].page_content.strip()[:1000]
            return f"Here is the most relevant content from the document:\n\n{context_snippet}"
        else:
            return "Not found in the documents."
    return raw_answer
