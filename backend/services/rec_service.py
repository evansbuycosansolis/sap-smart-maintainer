from services.vectorstore_manager import get_faiss_index, get_docs
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from config import OPENAI_API_KEY, prompt

async def contextual_recommendation(question, top_k=5):
    index = get_faiss_index()
    docs = get_docs()
    if not index or not docs:
        return {"error": "No vectorstore loaded. Please index documents first."}

    retriever = index.as_retriever(search_kwargs={"k": top_k})

    # 1. Get main LLM answer using RAG (same as global Q&A)
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )
    answer_result = await qa_chain.acall({"query": question})
    main_answer = answer_result['result'].strip()

    # 2. Get similar/relevant document chunks as recommendations
    similar_chunks = retriever.get_relevant_documents(question)
    recommendations = []
    for doc in similar_chunks:
        preview = doc.page_content[:400] + ("..." if len(doc.page_content) > 400 else "")
        rec = {
            "content": preview,
            "filename": doc.metadata.get("source", "Unknown"),
            "metadata": doc.metadata
        }
        recommendations.append(rec)
    return {
            "answer": main_answer,
            "recommendations": recommendations
        }


async def semantic_search(query, top_k=5):
    index = get_faiss_index()
    docs = get_docs()
    if not index or not docs:
        return []

    retriever = index.as_retriever(search_kwargs={"k": top_k})
    matched_docs = retriever.get_relevant_documents(query)
    results = []
    for doc in matched_docs:
        preview = doc.page_content[:400] + ("..." if len(doc.page_content) > 400 else "")
        result = {
            "content": preview,
            "filename": doc.metadata.get("source", "Unknown"),
            "metadata": doc.metadata
        }
        results.append(result)
    return results


