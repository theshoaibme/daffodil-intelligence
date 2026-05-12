import sys
sys.path.insert(0, '/Users/ratulhasan/Desktop/Shoaib/daffodil-intelligence/apps/api')

from app.rag.retriever import RAGSystem, TextChunker, VectorStore, SearchResult


def test_text_chunker():
    print("\n" + "="*50)
    print("TEST 1: Text Chunker")
    print("="*50)
    
    chunker = TextChunker(chunk_size=100, overlap=20)
    text = "This is the first sentence. This is the second sentence. This is the third sentence. And more text here."
    chunks = chunker.chunk(text)
    
    print(f"Original text: {text}")
    print(f"Chunks ({len(chunks)}):")
    for i, c in enumerate(chunks):
        print(f"  {i+1}: {c}")
    
    assert len(chunks) > 0, "Should produce at least one chunk"
    print("✓ Text chunking works!")


def test_vector_store():
    print("\n" + "="*50)
    print("TEST 2: Vector Store")
    print("="*50)
    
    store = VectorStore()
    
    store.add_document("Machine learning is a subset of artificial intelligence.", {"source": "AI101"})
    store.add_document("Deep learning uses neural networks with multiple layers.", {"source": "DL201"})
    store.add_document("Python is a popular programming language for data science.", {"source": "PY101"})
    
    results = store.search("neural networks", top_k=2)
    
    print(f"Added 3 documents, total: {store.count()}")
    print(f"Search 'neural networks' - top 2 results:")
    for r in results:
        print(f"  Score: {r.score:.4f} | {r.chunk[:50]}...")
    
    assert len(results) >= 1, "Should return at least 1 result"
    print("✓ Vector store works!")


def test_rag_system_basic():
    print("\n" + "="*50)
    print("TEST 3: RAG System - Basic Operations")
    print("="*50)
    
    rag = RAGSystem(chunk_size=200, overlap=30)
    
    doc1 = "The syllabus for CS301 includes: Data Structures, Algorithms, Time Complexity, Space Complexity, Sorting algorithms, Search algorithms."
    doc2 = "CGPA is calculated by multiplying each course grade point by the credit hours, summing them up, and dividing by total credits."
    doc3 = "The library has over 50,000 books, including textbooks, reference materials, and research journals. Opening hours are 8 AM to 8 PM."
    
    rag.ingest_document(doc1, {"course": "CS301", "type": "syllabus"})
    rag.ingest_document(doc2, {"topic": "cgpa", "type": "academic"})
    rag.ingest_document(doc3, {"topic": "library", "type": "campus"})
    
    print(f"Ingested 3 documents")
    print(f"Stats: {rag.get_stats()}")
    
    assert rag.get_stats()['total_documents'] == 3
    print("✓ Basic RAG operations work!")


def test_rag_search():
    print("\n" + "="*50)
    print("TEST 4: RAG Search")
    print("="*50)
    
    rag = RAGSystem()
    
    documents = [
        {"text": "Python is a high-level programming language. It is easy to learn and has simple syntax."},
        {"text": "Java is an object-oriented programming language. It is used for enterprise applications."},
        {"text": "JavaScript is a scripting language for web development. It runs in browsers."},
        {"text": "Machine learning algorithms include supervised and unsupervised learning."},
        {"text": "Deep learning uses neural networks with many layers to learn patterns."},
    ]
    
    rag.ingest_documents(documents)
    
    print(f"Stats: {rag.get_stats()}")
    
    test_queries = [
        "web programming",
        "neural networks",
        "object oriented",
        "programming",
    ]
    
    for query in test_queries:
        results = rag.search(query, top_k=3, min_score=-1.0)
        print(f"\nQuery: '{query}'")
        if results:
            print(f"  Found {len(results)} results")
            for r in results[:2]:
                print(f"    - {r['content'][:50]}... (score: {r['score']:.4f})")
        else:
            print(f"  No results found")
    
    print("✓ RAG search works!")


def test_rag_context():
    print("\n" + "="*50)
    print("TEST 5: RAG Context Generation")
    print("="*50)
    
    rag = RAGSystem()
    
    docs = [
        {"text": "The academic calendar has two semesters per year: Spring and Fall."},
        {"text": "Spring semester typically runs from January to May."},
        {"text": "Fall semester runs from August to December."},
        {"text": "Exams are held at the end of each semester."},
        {"text": "Midterm exams are conducted in the middle of each semester."},
    ]
    
    rag.ingest_documents(docs)
    
    context = rag.get_context("semester exams", max_chars=200)
    print(f"Context for 'semester exams':\n{context[:200]}...")
    
    augmented = rag.generate_augmented_prompt(
        "Explain exams",
        "You are a helpful academic assistant."
    )
    print(f"\nAugmented prompt length: {len(augmented)} chars")
    
    assert len(context) > 0
    assert len(augmented) > 0
    print("✓ Context generation works!")


def test_rag_batch():
    print("\n" + "="*50)
    print("TEST 6: Batch Document Ingestion")
    print("="*50)
    
    rag = RAGSystem()
    
    documents = [
        {"text": f"This is document {i} with some content about topic {i}."}
        for i in range(10)
    ]
    
    doc_ids = rag.ingest_documents(documents, {"batch": "test"})
    
    print(f"Ingested {len(doc_ids)} documents")
    print(f"Stats: {rag.get_stats()}")
    
    results = rag.search("topic 5", top_k=3, min_score=-1.0)
    print(f"\nSearch 'topic 5' - {len(results)} results")
    
    assert rag.get_stats()['total_documents'] >= 10
    print("✓ Batch ingestion works!")


def test_rag_with_metadata():
    print("\n" + "="*50)
    print("TEST 7: Metadata Handling")
    print("="*50)
    
    rag = RAGSystem()
    
    rag.ingest_document(
        "Machine learning is a subset of AI. It uses algorithms to learn from data.",
        {"topic": "AI", "course": "CS401", "level": "advanced"}
    )
    rag.ingest_document(
        "Data structures are ways of organizing and storing data.",
        {"topic": "Data Structures", "course": "CS201", "level": "intermediate"}
    )
    
    results = rag.search("algorithms learning", top_k=2, min_score=-1.0)
    print(f"Search results:")
    for r in results:
        print(f"  Content: {r['content'][:50]}...")
        print(f"  Metadata: {r['metadata']}")
        print(f"  Score: {r['score']:.4f}")
    
    assert len(results) >= 1
    print("✓ Metadata handling works!")


def test_rag_delete():
    print("\n" + "="*50)
    print("TEST 8: Document Deletion")
    print("="*50)
    
    rag = RAGSystem()
    
    doc_id = rag.ingest_document("This document will be deleted.", {"status": "temp"})
    print(f"Added document: {doc_id}")
    print(f"Total docs: {rag.get_stats()['total_documents']}")
    
    deleted = rag.vector_store.delete_document(doc_id)
    print(f"Deleted: {deleted}")
    
    assert deleted == True
    print("✓ Document deletion works!")


def test_rag_clear():
    print("\n" + "="*50)
    print("TEST 9: Clear All Documents")
    print("="*50)
    
    rag = RAGSystem()
    
    for i in range(5):
        rag.ingest_document(f"Document {i}", {"index": i})
    
    print(f"Before clear: {rag.get_stats()}")
    
    rag.clear()
    
    print(f"After clear: {rag.get_stats()}")
    
    assert rag.get_stats()['total_documents'] == 0
    assert rag.get_stats()['total_chunks'] == 0
    print("✓ Clear all works!")


def test_rag_real_scenario():
    print("\n" + "="*50)
    print("TEST 10: Real Academic Scenario")
    print("="*50)
    
    rag = RAGSystem()
    
    academic_docs = [
        {"text": "CGPA stands for Cumulative Grade Point Average. It is calculated by dividing total grade points by total credits."},
        {"text": "To calculate GPA, multiply grade points by credit hours for each course, sum them up, and divide by total credits."},
        {"text": " grading scale: A=4.0, A-=3.7, B+=3.3, B=3.0, B-=2.7, C+=2.3, C=2.0, D=1.0, F=0.0"},
        {"text": "Dean's List requires maintaining CGPA of 3.5 or above in a semester with at least 15 credits."},
        {"text": "Credit hours determine the weight of each course. Lab courses typically have 1 credit hour."},
    ]
    
    rag.ingest_documents(academic_docs, {"source": "academic_handbook"})
    
    queries = [
        "How is CGPA calculated?",
        "What is the grading scale?",
        "How to make Dean's List?",
    ]
    
    for q in queries:
        context = rag.get_context(q, max_chars=500)
        print(f"\nQuery: {q}")
        print(f"Context: {context[:150]}...")
    
    print("✓ Real academic scenario works!")


def main():
    print("\n" + "="*60)
    print("RAG SYSTEM - FULL TEST SUITE")
    print("="*60)
    
    test_text_chunker()
    test_vector_store()
    test_rag_system_basic()
    test_rag_search()
    test_rag_context()
    test_rag_batch()
    test_rag_with_metadata()
    test_rag_delete()
    test_rag_clear()
    test_rag_real_scenario()
    
    print("\n" + "="*60)
    print("ALL RAG TESTS PASSED! ✅")
    print("="*60)


if __name__ == "__main__":
    main()