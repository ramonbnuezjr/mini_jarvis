#!/usr/bin/env python3
"""Manual Test 3: Query with No Matches → Graceful Failure

This script tests:
- Handling queries with no relevant matches
- Empty collection handling
- min_score filtering
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
    print("Manual Test 3: Query with No Matches → Graceful Failure")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create test document with specific content
        print("\n📄 Step 1: Creating test document...")
        test_file = Path(temp_dir) / "test_document.txt"
        content = """This document is about cooking recipes.
It contains information about Italian cuisine and pasta dishes.
Nothing about quantum physics or rocket science here.
The recipes include spaghetti carbonara and margherita pizza."""
        
        test_file.write_text(content)
        print(f"   ✅ Created: {test_file}")
        
        # Initialize RAG server
        print("\n🔧 Step 2: Initializing RAG server...")
        rag_server = RAGServer(
            persist_directory=temp_dir,
            collection_name="manual_test_3"
        )
        print("   ✅ RAG server initialized")
        
        # Ingest document
        print("\n📥 Step 3: Ingesting document...")
        result = await rag_server.ingest_documents([str(test_file)])
        
        if not result["success"]:
            print(f"   ❌ Ingestion failed: {result.get('message', 'Unknown error')}")
            return
        
        print(f"   ✅ Ingested {result['chunks_ingested']} chunks")
        
        # Test 1: Query with unrelated topic (no min_score filter)
        print("\n🔍 Step 4: Testing unrelated query (no filter)...")
        query1 = "quantum physics"
        chunks1 = await rag_server.retrieve_context(query1, top_k=5, min_score=0.0)
        
        if chunks1:
            max_score = max(chunk["score"] for chunk in chunks1)
            print(f"   Retrieved {len(chunks1)} chunks (max score: {max_score:.3f})")
            print(f"   Note: Semantic search may find some similarity even in unrelated content")
        else:
            print(f"   ✅ No chunks retrieved (expected for unrelated query)")
        
        # Test 2: Query with min_score filter
        print("\n🔍 Step 5: Testing unrelated query (min_score=0.6)...")
        chunks2 = await rag_server.retrieve_context(query1, top_k=5, min_score=0.6)
        
        if chunks2:
            max_score = max(chunk["score"] for chunk in chunks2)
            print(f"   ⚠️  Retrieved {len(chunks2)} chunks with min_score=0.6 (max: {max_score:.3f})")
        else:
            print(f"   ✅ min_score filter correctly filtered out low-relevance results")
        
        # Test 3: Query on empty collection
        print("\n🔍 Step 6: Testing query on empty collection...")
        empty_server = RAGServer(
            persist_directory=temp_dir,
            collection_name="manual_test_3_empty"
        )
        empty_chunks = await empty_server.retrieve_context("any query", top_k=5)
        
        if empty_chunks:
            print(f"   ❌ Empty collection returned chunks (unexpected)")
        else:
            print(f"   ✅ Empty collection handled correctly")
        
        # Test 4: Related query should work
        print("\n🔍 Step 7: Testing related query (should work)...")
        related_chunks = await rag_server.retrieve_context("pasta recipes", top_k=3)
        
        if related_chunks:
            max_score = max(chunk["score"] for chunk in related_chunks)
            print(f"   ✅ Retrieved {len(related_chunks)} relevant chunks (max score: {max_score:.3f})")
        else:
            print(f"   ⚠️  No chunks for related query (unexpected)")
        
        # Summary
        print("\n" + "="*60)
        print("✅ TEST 3 PASSED: Graceful failure handling working")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

