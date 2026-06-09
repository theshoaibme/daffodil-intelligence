"""Qdrant vector store for agent memories with graceful fallback."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from ..core.config import get_settings
from .embeddings import embed_text, embedding_dim

logger = logging.getLogger(__name__)
settings = get_settings()


class QdrantMemoryStore:
    def __init__(self):
        self._client = None
        self._available = False
        self._collection = settings.MEMORY_QDRANT_COLLECTION
        self._init_attempted = False

    def _ensure_client(self) -> bool:
        if self._init_attempted:
            return self._available
        self._init_attempted = True

        if not settings.MEMORY_SEMANTIC_ENABLED:
            return False

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(url=settings.QDRANT_URL, timeout=5)
            collections = [c.name for c in self._client.get_collections().collections]
            if self._collection not in collections:
                self._client.create_collection(
                    collection_name=self._collection,
                    vectors_config=VectorParams(size=embedding_dim(), distance=Distance.COSINE),
                )
            self._available = True
            logger.info("Qdrant memory store connected: %s", self._collection)
        except Exception as e:
            logger.warning("Qdrant unavailable, using PG keyword fallback: %s", e)
            self._available = False
        return self._available

    @property
    def available(self) -> bool:
        return self._ensure_client()

    async def upsert(
        self,
        point_id: str,
        text: str,
        payload: Dict[str, Any],
    ) -> str:
        if not self._ensure_client():
            return point_id or str(uuid.uuid4())

        from qdrant_client.models import PointStruct

        vector = await embed_text(text)
        pid = point_id or str(uuid.uuid4())
        self._client.upsert(
            collection_name=self._collection,
            points=[PointStruct(id=pid, vector=vector, payload=payload)],
        )
        return pid

    async def search(
        self,
        query: str,
        *,
        user_id: int,
        agent_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        chat_id: Optional[Any] = None,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not self._ensure_client():
            return []

        from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

        must = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        if agent_id:
            must.append(FieldCondition(key="agent_id", match=MatchValue(value=agent_id)))
        if memory_types:
            must.append(FieldCondition(key="memory_type", match=MatchAny(any=memory_types)))
        if chat_id is not None:
            must.append(FieldCondition(key="chat_id", match=MatchValue(value=str(chat_id))))

        vector = await embed_text(query)
        response = self._client.query_points(
            collection_name=self._collection,
            query=vector,
            query_filter=Filter(must=must),
            limit=k,
            with_payload=True,
        )
        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload or {},
            }
            for hit in (response.points or [])
        ]

    def delete(self, point_id: str) -> None:
        if not self._ensure_client() or not point_id:
            return
        try:
            self._client.delete(
                collection_name=self._collection,
                points_selector=[point_id],
            )
        except Exception as e:
            logger.warning("Qdrant delete failed for %s: %s", point_id, e)

    def delete_many(self, point_ids: List[str]) -> None:
        ids = [pid for pid in point_ids if pid]
        if not ids or not self._ensure_client():
            return
        try:
            self._client.delete(
                collection_name=self._collection,
                points_selector=ids,
            )
        except Exception as e:
            logger.warning("Qdrant bulk delete failed for %d points: %s", len(ids), e)

    def delete_by_user(self, user_id: int) -> None:
        if not self._ensure_client():
            return
        try:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            self._client.delete(
                collection_name=self._collection,
                points_selector=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
            )
        except Exception as e:
            logger.warning("Qdrant bulk delete failed for user %s: %s", user_id, e)


qdrant_store = QdrantMemoryStore()
