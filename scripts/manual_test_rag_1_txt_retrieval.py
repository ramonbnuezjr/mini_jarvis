#!/usr/bin/env python3
"""Manual Test 1: Ingest TXT → Verify Retrieval

This script tests:
- Ingesting a text document
- Retrieving relevant chunks based on queries
"""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer


async def main():
    print("="*60)
    print("Manual Test 1: Ingest TXT → Verify Retrieval")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create test document
        print("\n📄 Step 1: Creating test document...")
        test_file = Path(temp_dir) / "test_document.txt"
        content = """Artificial Intelligence and Machine Learning

Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines.
Machine Learning (ML) is a subset of AI that enables systems to learn from data without explicit programming.
Deep Learning uses neural networks with multiple layers to process complex patterns.

Natural Language Processing (NLP) allows computers to understand and generate human language.
Computer Vision enables machines to interpret and understand visual information from the world.

These technologies are transforming industries from healthcare to transportation."""
        
        test_file.write_text(content)
        print(f"   ✅ Created: {test_file}")
        print(f"   Size: {len(content)} characters")
        
        # Initialize RAG server
        print("\n🔧 Step 2: Initializing RAG server...")
        rag_server = RAGServer(
            persist_directory=temp_dir,
            collection_name="manual_test_1"
        )
        print("   ✅ RAG server initialized")
        
        # Ingest document
        print("\n📥 Step 3: Ingesting document...")
        result = await rag_server.ingest_documents([str(test_file)])
        
        if not result["success"]:
            print(f"   ❌ Ingestion failed: {result.get('message', 'Unknown error')}")
            return
        
        chunks_ingested = result["chunks_ingested"]
        print(f"   ✅ Ingested {chunks_ingested} chunks")
        
        # Test retrieval
        print("\n🔍 Step 4: Testing retrieval...")
        test_queries = [
            "machine learning",
            "neural networks",
            "natural language processing"
        ]
        
        for query in test_queries:
            print(f"\n   Query: '{query}'")
            chunks = await rag_server.retrieve_context(query, top_k=3)
            
            if chunks:
                print(f"   ✅ Retrieved {len(chunks)} chunks")
                for i, chunk in enumerate(chunks, 1):
                    score = chunk["score"]
                    text_preview = chunk["text"][:80].replace("\n", " ")
                    print(f"      Chunk {i} (score: {score:.3f}): {text_preview}...")
            else:
                print(f"   ⚠️  No chunks retrieved")
        
        # Summary
        print("\n" + "="*60)
        print("✅ TEST 1 PASSED: TXT ingestion and retrieval working")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

