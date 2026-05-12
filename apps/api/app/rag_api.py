from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .core.security import get_current_user
from .rag.retriever import rag_system, RAGSystem

router = APIRouter(prefix="/rag", tags=["RAG"])


class DocumentInput(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentBatchInput(BaseModel):
    documents: List[DocumentInput]
    global_metadata: Optional[Dict[str, Any]] = None


class SearchInput(BaseModel):
    query: str
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.1


class PromptInput(BaseModel):
    query: str
    system_prompt: str
    max_context_chars: Optional[int] = 2000


@router.post("/documents")
async def add_document(
    doc: DocumentInput,
    user: dict = Depends(get_current_user)
):
    doc_id = rag_system.ingest_document(doc.text, doc.metadata)
    return {"doc_id": doc_id, "status": "added"}


@router.post("/documents/batch")
async def add_documents_batch(
    batch: DocumentBatchInput,
    user: dict = Depends(get_current_user)
):
    docs = [d.model_dump() for d in batch.documents]
    doc_ids = rag_system.ingest_documents(docs, batch.global_metadata)
    return {"doc_ids": doc_ids, "count": len(doc_ids)}


@router.post("/search")
async def search_documents(
    search: SearchInput,
    user: dict = Depends(get_current_user)
):
    results = rag_system.search(search.query, search.top_k, search.min_score)
    return {"results": results, "count": len(results)}


@router.post("/prompt")
async def generate_augmented_prompt(
    prompt: PromptInput,
    user: dict = Depends(get_current_user)
):
    augmented = rag_system.generate_augmented_prompt(prompt.query, prompt.system_prompt)
    return {"augmented_prompt": augmented}


@router.get("/context/{query}")
async def get_context(
    query: str,
    max_chars: int = 2000,
    user: dict = Depends(get_current_user)
):
    context = rag_system.get_context(query, max_chars)
    return {"context": context}


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    return rag_system.get_stats()


@router.delete("/clear")
async def clear_rag(user: dict = Depends(get_current_user)):
    rag_system.clear()
    return {"status": "cleared"}


@router.delete("/document/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    deleted = rag_system.vector_store.delete_document(doc_id)
    if doc_id in rag_system.document_store:
        del rag_system.document_store[doc_id]
    return {"deleted": deleted}


@router.get("/documents")
async def list_documents(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    docs = list(rag_system.document_store.items())[:limit]
    return {
        "documents": [
            {
                "doc_id": k,
                "chunk_count": v["chunk_count"],
                "metadata": v["metadata"],
                "preview": v["original_text"][:100] + "..."
            }
            for k, v in docs
        ]
    }