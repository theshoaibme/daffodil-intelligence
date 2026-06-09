"""
Unified Memory
==============
A single memory service combining:
  - durable conversation history (PostgreSQL Chat/Message) via the API layer
  - long-term semantic notes (Qdrant when available, JSON keyword fallback)
  - short-term context (handled by the Antigravity conversation store)

``MemoryService`` is the façade used by chat, telegram and voice.
"""

from .semantic import SemanticMemory, semantic_memory
from .service import MemoryService, memory_service
from .types import ALL_MEMORY_TYPES, ROOT_AGENT_ID

__all__ = [
    "SemanticMemory",
    "semantic_memory",
    "MemoryService",
    "memory_service",
    "ALL_MEMORY_TYPES",
    "ROOT_AGENT_ID",
]
