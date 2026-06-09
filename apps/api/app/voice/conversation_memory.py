import time
import os
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json
import hashlib


class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"


class MemoryPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class MemoryEntry:
    memory_id: str
    user_id: int
    content: str
    memory_type: MemoryType
    timestamp: float
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding_key: str = ""
    related_memories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def access(self):
        self.access_count += 1
        self.last_accessed = time.time()
    
    def get_key(self) -> str:
        return self.embedding_key or self._generate_key(self.content)
    
    def _generate_key(self, content: str) -> str:
        words = content.lower().split()[:5]
        return hashlib.md5(" ".join(words).encode()).hexdigest()[:16]


@dataclass
class ConversationContext:
    session_id: str
    user_id: int
    start_time: float
    messages: List[Dict] = field(default_factory=list)
    short_term_memory: List[MemoryEntry] = field(default_factory=list)
    context_window: int = 10
    total_turns: int = 0
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        })
        self.total_turns += 1
        
        if len(self.messages) > self.context_window:
            self.messages = self.messages[-self.context_window:]


def serialize_entry(entry: MemoryEntry) -> dict:
    return {
        "memory_id": entry.memory_id,
        "user_id": entry.user_id,
        "content": entry.content,
        "memory_type": entry.memory_type.value,
        "timestamp": entry.timestamp,
        "importance_score": entry.importance_score,
        "access_count": entry.access_count,
        "last_accessed": entry.last_accessed,
        "metadata": entry.metadata,
        "embedding_key": entry.embedding_key,
        "related_memories": entry.related_memories,
        "tags": entry.tags,
    }


def deserialize_entry(d: dict) -> MemoryEntry:
    return MemoryEntry(
        memory_id=d["memory_id"],
        user_id=d["user_id"],
        content=d["content"],
        memory_type=MemoryType(d["memory_type"]),
        timestamp=d["timestamp"],
        importance_score=d.get("importance_score", 0.5),
        access_count=d.get("access_count", 0),
        last_accessed=d.get("last_accessed", 0.0),
        metadata=d.get("metadata", {}),
        embedding_key=d.get("embedding_key", ""),
        related_memories=d.get("related_memories", []),
        tags=d.get("tags", []),
    )


class ConversationMemory:
    def __init__(self):
        self.short_term: Dict[int, deque] = {}
        self.long_term: Dict[int, List[MemoryEntry]] = {}
        self.episodic: Dict[int, List[Dict]] = {}
        self.semantic: Dict[int, Dict[str, MemoryEntry]] = {}
        self.working: Dict[int, List[MemoryEntry]] = {}
        
        self.max_short_term = 50
        self.max_working = 10
        self.context_window = 10
        self.importance_threshold = 0.3
        self.forgetting_rate = 0.01
        
        self._memory_index: Dict[int, Dict[str, List[str]]] = {}

    def save_to_disk(self):
        """Voice memory is in-process only; durable storage uses agent_memories (PostgreSQL)."""
        return

    def load_from_disk(self):
        return

    def _load_from_disk_legacy(self):
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "agent_memory.json")
            if not os.path.exists(file_path):
                return
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.short_term = {}
            for uid_str, entries in data.get("short_term", {}).items():
                uid = int(uid_str)
                self.short_term[uid] = deque(
                    [deserialize_entry(e) for e in entries],
                    maxlen=self.max_short_term
                )
            
            self.long_term = {}
            for uid_str, entries in data.get("long_term", {}).items():
                uid = int(uid_str)
                self.long_term[uid] = [deserialize_entry(e) for e in entries]
            
            self.episodic = {}
            for uid_str, episodes in data.get("episodic", {}).items():
                uid = int(uid_str)
                self.episodic[uid] = episodes
            
            self.semantic = {}
            for uid_str, dct in data.get("semantic", {}).items():
                uid = int(uid_str)
                self.semantic[uid] = {k: deserialize_entry(e) for k, e in dct.items()}
                
            self.working = {}
            for uid_str, entries in data.get("working", {}).items():
                uid = int(uid_str)
                self.working[uid] = [deserialize_entry(e) for e in entries]
        except Exception as e:
            print(f"Error loading agent memory from disk: {e}")
    
    def _get_or_create_short_term(self, user_id: int) -> deque:
        if user_id not in self.short_term:
            self.short_term[user_id] = deque(maxlen=self.max_short_term)
        return self.short_term[user_id]
    
    def _get_or_create_long_term(self, user_id: int) -> List[MemoryEntry]:
        if user_id not in self.long_term:
            self.long_term[user_id] = []
        return self.long_term[user_id]
    
    def add_to_memory(
        self,
        user_id: int,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        metadata: Dict = None,
        tags: List[str] = None
    ) -> MemoryEntry:
        memory_id = f"mem_{user_id}_{int(time.time() * 1000)}"
        
        entry = MemoryEntry(
            memory_id=memory_id,
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            importance_score=importance,
            metadata=metadata or {},
            tags=tags or []
        )
        
        entry.embedding_key = entry.get_key()
        
        if memory_type == MemoryType.SHORT_TERM:
            short_term = self._get_or_create_short_term(user_id)
            short_term.append(entry)
        elif memory_type == MemoryType.LONG_TERM:
            long_term = self._get_or_create_long_term(user_id)
            long_term.append(entry)
            self._update_semantic_index(user_id, entry)
        elif memory_type == MemoryType.WORKING:
            if user_id not in self.working:
                self.working[user_id] = []
            self.working[user_id].append(entry)
        
        self.save_to_disk()
        return entry
    
    def _update_semantic_index(self, user_id: int, entry: MemoryEntry):
        if user_id not in self.semantic:
            self.semantic[user_id] = {}
        
        key = entry.embedding_key
        if key in self.semantic[user_id]:
            existing = self.semantic[user_id][key]
            existing.importance_score = max(existing.importance_score, entry.importance_score)
        else:
            self.semantic[user_id][key] = entry
    
    def retrieve_relevant(
        self,
        user_id: int,
        query: str,
        memory_type: MemoryType = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        results = []
        
        query_words = set(query.lower().split())
        
        search_lists = []
        if memory_type == MemoryType.SHORT_TERM:
            search_lists.append(self._get_or_create_short_term(user_id))
        elif memory_type == MemoryType.LONG_TERM:
            search_lists.append(self._get_or_create_long_term(user_id))
        elif memory_type == MemoryType.SEMANTIC:
            search_lists.append(list(self.semantic.get(user_id, {}).values()))
        else:
            search_lists.append(self._get_or_create_short_term(user_id))
            search_lists.append(self._get_or_create_long_term(user_id))
        
        for mem_list in search_lists:
            for entry in mem_list:
                if entry.user_id != user_id:
                    continue
                
                content_words = set(entry.content.lower().split())
                overlap = len(query_words & content_words)
                
                if overlap > 0:
                    relevance = overlap / max(len(query_words), 1)
                    results.append((entry, relevance * entry.importance_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [entry for entry, score in results[:limit]]
    
    def get_context_for_response(
        self,
        user_id: int,
        current_message: str,
        include_short_term: bool = True,
        include_long_term: bool = True
    ) -> str:
        context_parts = []
        
        if include_short_term:
            short_term = self._get_or_create_short_term(user_id)
            recent_memories = list(short_term)[-5:]
            
            if recent_memories:
                context_parts.append("Recent context:")
                for mem in recent_memories:
                    context_parts.append(f"- {mem.content}")
        
        if include_long_term:
            relevant = self.retrieve_relevant(
                user_id,
                current_message,
                memory_type=MemoryType.SEMANTIC,
                limit=3
            )
            
            if relevant:
                context_parts.append("\nRelevant memories:")
                for mem in relevant:
                    context_parts.append(f"- {mem.content}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def consolidate_to_long_term(self, user_id: int) -> int:
        short_term = self._get_or_create_short_term(user_id)
        long_term = self._get_or_create_long_term(user_id)
        
        consolidated = 0
        to_remove = []
        
        for entry in short_term:
            if entry.importance_score >= self.importance_threshold:
                long_term.append(entry)
                self._update_semantic_index(user_id, entry)
                to_remove.append(entry)
                consolidated += 1
        
        for entry in to_remove:
            short_term.remove(entry)
        
        if consolidated > 0:
            self.save_to_disk()
        return consolidated
    
    def forget_old_memories(self, user_id: int, max_age_seconds: float = 3600):
        current_time = time.time()
        
        short_term = self._get_or_create_short_term(user_id)
        to_remove = []
        
        for entry in short_term:
            age = current_time - entry.timestamp
            decay = self.forgetting_rate * (age / 60)
            entry.importance_score *= (1 - decay)
            
            if entry.importance_score < 0.1:
                to_remove.append(entry)
        
        for entry in to_remove:
            short_term.remove(entry)
        
        self.save_to_disk()
        return len(to_remove)
    
    def create_episode(self, user_id: int, session_id: str, context: ConversationContext):
        if user_id not in self.episodic:
            self.episodic[user_id] = []
        
        episode = {
            "episode_id": f"ep_{session_id}_{int(time.time() * 1000)}",
            "session_id": session_id,
            "start_time": context.start_time,
            "end_time": time.time(),
            "turns": context.total_turns,
            "message_count": len(context.messages),
            "summary": self._generate_summary(context.messages),
            "entities": self._extract_entities(context.messages),
            "sentiment": self._analyze_sentiment(context.messages)
        }
        
        self.episodic[user_id].append(episode)
        
        if len(self.episodic[user_id]) > 100:
            self.episodic[user_id] = self.episodic[user_id][-100:]
        
        self.save_to_disk()
        return episode
    
    def _generate_summary(self, messages: List[Dict]) -> str:
        if not messages:
            return ""
        
        first_msg = messages[0].get("content", "")[:50]
        last_msg = messages[-1].get("content", "")[:50]
        
        return f"Conversation from {first_msg}... to {last_msg}"
    
    def _extract_entities(self, messages: List[Dict]) -> List[str]:
        entities = []
        for msg in messages:
            content = msg.get("content", "")
            words = content.split()
            for word in words:
                if word and word[0].isupper() and len(word) > 2:
                    if word not in entities:
                        entities.append(word)
        return entities[:20]
    
    def _analyze_sentiment(self, messages: List[Dict]) -> str:
        positive_words = ["good", "great", "thanks", "love", "happy", "perfect"]
        negative_words = ["bad", "sad", "hate", "angry", "frustrated", "wrong"]
        
        pos_count = 0
        neg_count = 0
        
        for msg in messages:
            content = msg.get("content", "").lower()
            pos_count += sum(1 for w in positive_words if w in content)
            neg_count += sum(1 for w in negative_words if w in content)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
    
    def get_episode_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        episodes = self.episodic.get(user_id, [])
        return episodes[-limit:]
    
    def search_memories(self, user_id: int, query: str, limit: int = 20) -> List[Dict]:
        results = []
        
        all_memories = (
            list(self._get_or_create_short_term(user_id)) +
            self._get_or_create_long_term(user_id) +
            list(self.semantic.get(user_id, {}).values())
        )
        
        query_lower = query.lower()
        
        for entry in all_memories:
            if entry.user_id != user_id:
                continue
            
            if query_lower in entry.content.lower():
                results.append({
                    "memory_id": entry.memory_id,
                    "content": entry.content,
                    "type": entry.memory_type.value,
                    "timestamp": entry.timestamp,
                    "importance": entry.importance_score,
                    "tags": entry.tags
                })
        
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return results[:limit]
    
    def clear_short_term(self, user_id: int):
        if user_id in self.short_term:
            self.short_term[user_id].clear()
            self.save_to_disk()
    
    def clear_all_memory(self, user_id: int):
        self.short_term.pop(user_id, None)
        self.long_term.pop(user_id, None)
        self.episodic.pop(user_id, None)
        self.semantic.pop(user_id, None)
        self.working.pop(user_id, None)
        self.save_to_disk()
    
    def get_memory_stats(self, user_id: int) -> Dict[str, Any]:
        return {
            "short_term_count": len(self._get_or_create_short_term(user_id)),
            "long_term_count": len(self._get_or_create_long_term(user_id)),
            "episode_count": len(self.episodic.get(user_id, [])),
            "semantic_count": len(self.semantic.get(user_id, {})),
            "working_count": len(self.working.get(user_id, [])),
            "total_memories": (
                len(self._get_or_create_short_term(user_id)) +
                len(self._get_or_create_long_term(user_id)) +
                len(self.episodic.get(user_id, []))
            )
        }
    
    def update_memory_importance(self, user_id: int, memory_id: str, delta: float):
        for mem_list in [
            self._get_or_create_short_term(user_id),
            self._get_or_create_long_term(user_id)
        ]:
            for entry in mem_list:
                if entry.memory_id == memory_id:
                    entry.importance_score = max(0, min(1, entry.importance_score + delta))
                    self.save_to_disk()
                    return True
        return False
    
    def get_recent_context(self, user_id: int, turns: int = 5) -> List[Dict]:
        short_term = self._get_or_create_short_term(user_id)
        recent = list(short_term)[-turns:]
        
        return [
            {
                "content": m.content,
                "timestamp": m.timestamp,
                "type": m.memory_type.value
            }
            for m in recent
        ]
    
    def add_with_context_window(
        self,
        user_id: int,
        content: str,
        window_size: int = None
    ):
        if window_size:
            self.context_window = window_size
        
        entry = self.add_to_memory(
            user_id,
            content,
            memory_type=MemoryType.SHORT_TERM,
            importance=0.5
        )
        
        self.forget_old_memories(user_id)
        
        if len(self._get_or_create_short_term(user_id)) >= self.context_window:
            self.consolidate_to_long_term(user_id)
        
        return entry
    
    def get_memory_by_id(self, user_id: int, memory_id: str) -> Optional[MemoryEntry]:
        for mem_list in [
            self._get_or_create_short_term(user_id),
            self._get_or_create_long_term(user_id)
        ]:
            for entry in mem_list:
                if entry.memory_id == memory_id:
                    entry.access()
                    return entry
        return None
    
    def link_memories(self, memory_id1: str, memory_id2: str, user_id: int):
        entry1 = self.get_memory_by_id(user_id, memory_id1)
        entry2 = self.get_memory_by_id(user_id, memory_id2)
        
        if entry1 and entry2:
            if memory_id2 not in entry1.related_memories:
                entry1.related_memories.append(memory_id2)
            if memory_id1 not in entry2.related_memories:
                entry2.related_memories.append(memory_id1)
            self.save_to_disk()
            return True
        return False
    
    def get_related_memories(self, user_id: int, memory_id: str) -> List[MemoryEntry]:
        entry = self.get_memory_by_id(user_id, memory_id)
        if not entry:
            return []
        
        related = []
        for rel_id in entry.related_memories:
            rel_entry = self.get_memory_by_id(user_id, rel_id)
            if rel_entry:
                related.append(rel_entry)
        
        return related


conversation_memory = ConversationMemory()