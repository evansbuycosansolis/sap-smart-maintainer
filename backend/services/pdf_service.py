# backend/services/pdf_service.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv
from services.s3_service import (
    upload_pdf_to_s3,
    download_file_from_s3,
    list_pdfs_in_s3,
    sanitize_s3_folder_name,  # Import the sanitizer!
)
from fastapi.concurrency import run_in_threadpool

# ======================================================================
# ==== Environment and constants ====
# ======================================================================
dotenv_path = find_dotenv()
load_dotenv(dotenv_path, override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTORSTORE_PATH = "vectorstore/faiss_index"
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def get_temp_path(filename):
    temp_folder = os.path.join(os.getcwd(), "tmp")
    os.makedirs(temp_folder, exist_ok=True)
    return os.path.join(temp_folder, filename)

# ======================================================================
# ====== Custom PromptTemplate for RetrievalQA ======
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
# ---- 1. PDF Upload and Indexing ----
# ======================================================================
def process_and_index_pdf(pdf_file, pdf_filename, category=None, skip_s3_upload=False):
    """
    Upload PDF to S3 (optionally to a sanitized category/folder), index it, and update vectorstore.
    If skip_s3_upload=True, skip the upload step (for PDFs already in S3).
    """
    sanitized_category = sanitize_s3_folder_name(category) if category else None

    if not skip_s3_upload:
        pdf_file.seek(0)
        upload_success = upload_pdf_to_s3(pdf_file, pdf_filename, folder=sanitized_category)
        if not upload_success:
            return False, "Upload to S3 failed."

    temp_path = get_temp_path(pdf_filename)
    # Always (re)download from S3 to ensure fresh copy for indexing
    download_success = download_file_from_s3(pdf_filename, temp_path, folder=sanitized_category)
    if not download_success:
        return False, "Failed to download PDF from S3 for indexing."

    loader = PyPDFLoader(temp_path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    if os.path.exists(VECTORSTORE_PATH):
        vectorstore = FAISS.load_local(
            VECTORSTORE_PATH, embedding_model, allow_dangerous_deserialization=True
        )
        vectorstore.add_texts(
            [doc.page_content for doc in chunks],
            metadatas=[doc.metadata for doc in chunks]
        )
    else:
        vectorstore = FAISS.from_documents(chunks, embedding_model)
    vectorstore.save_local(VECTORSTORE_PATH)

    if os.path.exists(temp_path):
        os.remove(temp_path)
    return True, "PDF indexed successfully." if skip_s3_upload else "PDF uploaded and indexed successfully."


# ======================================================================
# ---- 2. Single PDF Q&A ----
# ======================================================================
async def ask_pdf(question, filename, category=None):
    """
    Answer a question for a single PDF (optionally specifying a sanitized category/folder).
    """
    temp_path = get_temp_path(filename)
    sanitized_category = sanitize_s3_folder_name(category) if category else None
    download_success = download_file_from_s3(filename, temp_path, folder=sanitized_category)
    if not download_success:
        return "Error downloading PDF from S3."

    loader = PyPDFLoader(temp_path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    for chunk in chunks:
        chunk.metadata["source"] = filename

    if not chunks:
        return "PDF appears empty or unreadable."

    vectorstore = FAISS.from_documents(chunks, embedding_model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    retrieved_docs = retriever.get_relevant_documents(question)

    if not retrieved_docs or not any(d.page_content.strip() for d in retrieved_docs):
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return "Not found in the document."

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

    if os.path.exists(temp_path):
        os.remove(temp_path)

    if not raw_answer or "not found" in raw_answer.lower():
        if retrieved_docs and any(d.page_content.strip() for d in retrieved_docs):
            context_snippet = retrieved_docs[0].page_content.strip()[:1000]
            return f"Direct answer not found. Here is the most relevant content from the document:\n\n{context_snippet}"
        else:
            return "Not found in the document."
    return raw_answer

# ======================================================================
# ---- 3. Ask Across All PDFs ----
# ======================================================================
async def ask_all_pdfs(question, category=None):
    """
    Answer a question across all PDFs (optionally restricted to a sanitized category/folder).
    """
    sanitized_category = sanitize_s3_folder_name(category) if category else ""
    pdf_filenames = list_pdfs_in_s3(prefix=sanitized_category)
    print("DEBUG: S3 found these PDFs:", pdf_filenames)

    if not pdf_filenames:
        return "No PDF documents found in S3 bucket."
    all_docs = []
    temp_paths = []
    for filename in pdf_filenames:
        fname = filename.split("/")[-1]  # Remove prefix if present
        temp_path = get_temp_path(fname)
        temp_paths.append(temp_path)
        download_success = download_file_from_s3(fname, temp_path, folder=sanitized_category)
        if not download_success:
            continue
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = fname
        all_docs.extend(docs)
    if not all_docs:
        return "No readable PDF documents found in S3 bucket."

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)

    # Filter for file if question contains a filename
    file_filter = None
    for fname in pdf_filenames:
        name_clean = fname.lower().replace(".pdf", "").replace("_", " ").replace("-", " ")
        if name_clean in question.lower().replace("_", " ").replace("-", " "):
            file_filter = fname
            break

    if file_filter:
        filtered_chunks = [chunk for chunk in chunks if chunk.metadata.get("source") == file_filter.split("/")[-1]]
        if not filtered_chunks:
            return f"No content found for {file_filter}."
        from langchain.schema import Document
        combined_text = "\n\n".join([chunk.page_content for chunk in filtered_chunks])
        full_doc = Document(page_content=combined_text, metadata={"source": file_filter.split("/")[-1]})
        chunks = [full_doc]

    if not chunks:
        return "No readable content in any PDF."

    vectorstore = FAISS.from_documents(chunks, embedding_model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    retrieved_docs = retriever.get_relevant_documents(question)

    if not retrieved_docs or not any(d.page_content.strip() for d in retrieved_docs):
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
        return "Not found in the documents."

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

    for path in temp_paths:
        if os.path.exists(path):
            os.remove(path)

    if not raw_answer or "not found" in raw_answer.lower():
        if retrieved_docs and any(d.page_content.strip() for d in retrieved_docs):
            context_snippet = retrieved_docs[0].page_content.strip()[:1000]
            return f"Direct answer not found. Here is the most relevant content from the document:\n\n{context_snippet}"
        else:
            return "Not found in the documents."
    return raw_answer
# ======================================================================