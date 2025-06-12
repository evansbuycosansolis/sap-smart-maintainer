# backend/services/vectorstore_manager.py

import os
import pickle
from langchain_community.vectorstores import FAISS
from config import VECTORSTORE_PATH, embedding_model

# Singleton variables
_VECTORSTORE = None
_DOCS = None

def load_faiss_index():
    """
    Loads (or reloads) the FAISS index and docs metadata into memory.
    """
    print("Using vectorstore_manager.py version 1.0")
    global _VECTORSTORE, _DOCS
    index_path = VECTORSTORE_PATH
    docs_path = os.path.join(os.path.dirname(index_path), "docs.pkl")
    if os.path.exists(index_path) and os.path.exists(docs_path):
        print(f"[FAISS MANAGER] Loading FAISS index from {index_path}")
        with open(docs_path, "rb") as f:
            _DOCS = pickle.load(f)
        _VECTORSTORE = FAISS.load_local(
            index_path,
            embedding_model,
            allow_dangerous_deserialization=True,
        )
        print("[FAISS MANAGER] FAISS index loaded and ready.")
        return True
    else:
        print("[FAISS MANAGER] No FAISS index found on disk.")
        _VECTORSTORE, _DOCS = None, None
        return False


def get_faiss_index():
    """
    Returns the loaded FAISS index, or None if not loaded.
    """
    return _VECTORSTORE

def get_docs():
    return _DOCS

def save_faiss_index(vectorstore, docs):
    """
    Save the FAISS index and document metadata, then update in-memory singleton.
    """
    index_path = VECTORSTORE_PATH
    docs_path = os.path.join(os.path.dirname(index_path), "docs.pkl")
    vectorstore.save_local(index_path)
    with open(docs_path, "wb") as f:
        pickle.dump(docs, f)
    print("[FAISS MANAGER] Index and docs saved to disk.")
    # Refresh the singleton
    global _VECTORSTORE, _DOCS
    _VECTORSTORE = vectorstore
    _DOCS = docs

def reset_faiss_index():
    """
    Clears the in-memory index and docs.
    """
    global _VECTORSTORE, _DOCS
    _VECTORSTORE, _DOCS = None, None

