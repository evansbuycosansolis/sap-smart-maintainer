# backend/utils/chunking.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document

# ======================================================================
# ==== Utility Functions for Chunking PDFs ====
# ======================================================================
def get_temp_path(filename):
    """Create a tmp folder (if not exists) and return the full path for the given filename."""
    temp_folder = os.path.join(os.getcwd(), "tmp")
    os.makedirs(temp_folder, exist_ok=True)
    return os.path.join(temp_folder, filename)

# ======================================================================
# ==== Load and Split PDF into Chunks ====
# ======================================================================
def load_and_split_pdf(local_path, chunk_size=1000, chunk_overlap=200):
    """
    Loads a PDF from local_path, splits it into chunks using CharacterTextSplitter,
    and returns a list of Document chunks.
    """
    loader = PyPDFLoader(local_path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)
    return chunks

# ======================================================================
# ==== Merge Chunks into a Single Document ====
# ======================================================================
def merge_chunks_to_single_doc(chunks, metadata=None):
    """
    Concatenate all chunks' text into a single Document for LLM context.
    """
    if not chunks:
        return Document(page_content="", metadata=metadata or {})
    combined_text = "\n\n".join([chunk.page_content for chunk in chunks])
    meta = metadata if metadata else (chunks[0].metadata if chunks else {})
    return Document(page_content=combined_text, metadata=meta)
# ======================================================================
