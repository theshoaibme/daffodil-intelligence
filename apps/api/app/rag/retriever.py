import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import hashlib
import re


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Any = None


@dataclass
class SearchResult:
    document: Document
    score: float
    chunk: str


class TextChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                overlap_text = ' '.join(current_chunk)[-self.overlap:] if len(current_chunk) > 1 else ''
                current_chunk = [overlap_text + sentence] if overlap_text else [sentence]
                current_size = len(overlap_text) + sentence_size if overlap_text else sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return [c for c in chunks if c.strip()]


class SimpleEmbeddings:
    def __init__(self, dim: int = 384):
        self.dim = dim
        np.random.seed(42)

    def embed(self, text: str) -> np.ndarray:
        text_hash = hashlib.md5(text.encode()).digest()
        seed = int.from_bytes(text_hash[:4], 'little')
        rng = np.random.RandomState(seed)
        embedding = rng.randn(self.dim)
        return embedding / np.linalg.norm(embedding)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        return [self.embed(text) for text in texts]


class VectorStore:
    def __init__(self, dimensions: int = 384):
        self.documents: Dict[str, Document] = {}
        self.dimensions = dimensions
        self.embeddings = SimpleEmbeddings(dim=dimensions)

    def add_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        doc_id = hashlib.md5(content.encode()).hexdigest()[:12]
        if doc_id in self.documents:
            return doc_id

        embedding = self.embeddings.embed(content)
        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {},
            embedding=embedding
        )
        self.documents[doc_id] = doc
        return doc_id

    def add_documents_batch(self, contents: List[str], metadata: Dict[str, Any] = None) -> List[str]:
        embeddings = self.embeddings.embed_batch(contents)
        doc_ids = []
        for i, (content, embedding) in enumerate(zip(contents, embeddings)):
            doc_id = hashlib.md5(content.encode()).hexdigest()[:12]
            if doc_id not in self.documents:
                meta = metadata.copy() if metadata else {}
                meta['index'] = i
                doc = Document(
                    id=doc_id,
                    content=content,
                    metadata=meta,
                    embedding=embedding
                )
                self.documents[doc_id] = doc
            doc_ids.append(doc_id)
        return doc_ids

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if not self.documents:
            return []

        query_embedding = self.embeddings.embed(query)
        results = []

        for doc in self.documents.values():
            if doc.embedding is None:
                continue
            similarity = np.dot(query_embedding, doc.embedding)
            results.append(SearchResult(document=doc, score=similarity, chunk=doc.content))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self.documents.get(doc_id)

    def get_all_documents(self) -> List[Document]:
        return list(self.documents.values())

    def count(self) -> int:
        return len(self.documents)


class RAGSystem:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.vector_store = VectorStore()
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        self.document_store: Dict[str, Dict] = {}

    def ingest_document(self, text: str, metadata: Dict[str, Any] = None, chunk: bool = True) -> str:
        doc_id = hashlib.md5(text.encode()).hexdigest()[:12]

        if chunk:
            chunks = self.chunker.chunk(text)
            self.vector_store.add_documents_batch(chunks, metadata)
            self.document_store[doc_id] = {
                'original_text': text,
                'chunks': chunks,
                'metadata': metadata or {},
                'chunk_count': len(chunks)
            }
        else:
            self.vector_store.add_document(text, metadata)
            self.document_store[doc_id] = {
                'original_text': text,
                'chunks': [text],
                'metadata': metadata or {},
                'chunk_count': 1
            }

        return doc_id

    def ingest_documents(self, documents: List[Dict[str, str]], metadata: Dict[str, Any] = None) -> List[str]:
        doc_ids = []
        for doc in documents:
            text = doc.get('text', doc.get('content', ''))
            meta = {**(metadata or {}), **(doc.get('metadata', {}))}
            doc_id = self.ingest_document(text, meta)
            doc_ids.append(doc_id)
        return doc_ids

    def search(self, query: str, top_k: int = 5, min_score: float = 0.1) -> List[Dict[str, Any]]:
        results = self.vector_store.search(query, top_k)
        
        formatted_results = []
        for r in results:
            if r.score >= min_score:
                formatted_results.append({
                    'content': r.chunk,
                    'score': float(r.score),
                    'metadata': r.document.metadata
                })
        
        return formatted_results

    def get_context(self, query: str, max_chars: int = 2000) -> str:
        results = self.search(query, top_k=5, min_score=-1.0)
        context_parts = []
        total_chars = 0

        for r in results:
            if total_chars + len(r['content']) > max_chars:
                break
            context_parts.append(r['content'])
            total_chars += len(r['content'])

        return '\n\n'.join(context_parts)

    def generate_augmented_prompt(self, query: str, system_prompt: str) -> str:
        context = self.get_context(query)
        return f"{system_prompt}\n\nContext:\n{context}\n\nUser Query: {query}"

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_documents': len(self.document_store),
            'total_chunks': self.vector_store.count(),
            'chunk_size': self.chunker.chunk_size,
            'overlap': self.chunker.overlap
        }

    def clear(self):
        self.vector_store = VectorStore()
        self.document_store = {}


rag_system = RAGSystem()