# backend/api/rec_routes.py

from fastapi import APIRouter, Request
from services.rec_service import contextual_recommendation, semantic_search

router = APIRouter()

@router.post("/api/contextual-recommendation/")
async def contextual_recommendation_route(request: Request):
    data = await request.json()
    question = data.get("question")
    if not question:
        return {"error": "Missing question."}
    result = await contextual_recommendation(question)
    return result

@router.post("/api/semantic-search/")
async def semantic_search_route(request: Request):
    data = await request.json()
    query = data.get("query")
    if not query:
        return {"error": "Missing query."}
    results = await semantic_search(query)
    return {"results": results}
