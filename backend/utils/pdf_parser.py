from langchain_community.document_loaders import PyPDFLoader

def parse_pdf_to_text(pdf_path):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    # Concatenate all pages
    return "\n".join([doc.page_content for doc in docs])
