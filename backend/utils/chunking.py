# /backend/utils/chunking.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document

def get_temp_path(filename):
    """Create and return a temp file path in ./tmp/."""
    temp_folder = os.path.join(os.getcwd(), "tmp")
    os.makedirs(temp_folder, exist_ok=True)
    return os.path.join(temp_folder, filename)

def load_and_split_pdf(local_path, chunk_size=1000, chunk_overlap=200):
    """
    Load a PDF and split it into chunks.
    Returns: list of Document chunks
    """
    loader = PyPDFLoader(local_path)
    docs = loader.load()
    splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(docs)

def merge_chunks_to_single_doc(chunks, metadata=None):
    """
    Combine multiple Document chunks into a single Document.
    """
    if not chunks:
        return Document(page_content="", metadata=metadata or {})
    combined_text = "\n\n".join([chunk.page_content for chunk in chunks])
    meta = metadata if metadata else (chunks[0].metadata if chunks else {})
    return Document(page_content=combined_text, metadata=meta)
