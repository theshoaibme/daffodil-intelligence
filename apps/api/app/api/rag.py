from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import Document
from ..rag.retriever import rag_system
import aiofiles

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "general",
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    doc = Document(title=file.filename, content=text[:10000], doc_type=doc_type)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        rag_system.add_document(text, {"doc_id": doc.id, "title": file.filename})
    except Exception as e:
        pass

    return {"doc_id": doc.id, "status": "uploaded"}


@router.post("/search")
async def search_documents(
    query: str,
    top_k: int = 3,
    user: dict = Depends(get_current_user)
):
    try:
        results = rag_system.search(query, top_k)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()).limit(50))
    docs = result.scalars().all()
    return [
        {"id": d.id, "title": d.title, "doc_type": d.doc_type, "created_at": d.created_at.isoformat()}
        for d in docs
    ]