import os
import pickle
from glob import glob
from langchain_community.vectorstores.faiss import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings  # or your embedding class
from dotenv import load_dotenv

# --------------- CONFIGURE THESE ---------------
PDF_FOLDER = "./pdfs"  # path to your local folder containing PDFs
INDEX_DIR = "faiss_index"  # output directory for FAISS index and docs.pkl
load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set!")
EMBEDDING_MODEL = OpenAIEmbeddings(openai_api_key=openai_api_key)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
# -----------------------------------------------

def get_all_pdfs(pdf_folder):
    return glob(os.path.join(pdf_folder, "*.pdf"))

def main():
    all_docs = []
    for pdf_path in get_all_pdfs(PDF_FOLDER):
        fname = os.path.basename(pdf_path)
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = fname
        all_docs.extend(docs)
        print(f"Loaded {fname} with {len(docs)} docs")

    if not all_docs:
        print("No PDFs found!")
        return

    print(f"Splitting {len(all_docs)} docs...")
    splitter = CharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(all_docs)
    print(f"Got {len(chunks)} chunks.")

    print("Embedding chunks (this may take a while)...")
    docs = chunks
    # Batch embedding
    texts = [doc.page_content for doc in docs]
    embeddings = EMBEDDING_MODEL.embed_documents(texts)
    print("Embeddings done.")

    print("Building FAISS index...")
    text_embeddings = list(zip(texts, embeddings))
    vectorstore = FAISS.from_embeddings(text_embeddings, EMBEDDING_MODEL)
    vectorstore.save_local(INDEX_DIR)
    print(f"FAISS index saved to {INDEX_DIR}")

    docs_path = os.path.join(INDEX_DIR, "docs.pkl")
    with open(docs_path, "wb") as f:
        pickle.dump(docs, f)
    print(f"Document metadata saved to {docs_path}")

if __name__ == "__main__":
    main()
