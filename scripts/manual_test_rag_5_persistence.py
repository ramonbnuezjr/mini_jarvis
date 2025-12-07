#!/usr/bin/env python3
"""Manual Test 5: Reboot → Persistence Check

This script tests:
- Data persistence across server restarts
- ChromaDB persistence
- Retrieval after "reboot"
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
    print("Manual Test 5: Reboot → Persistence Check")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create test document
        print("\n📄 Step 1: Creating test document...")
        test_file = Path(temp_dir) / "persistence_test.txt"
        content = """Persistence Test Document

This document tests whether RAG data persists across server restarts.
The data should be stored in ChromaDB and survive server restarts.
This is critical for long-term memory functionality.
The system must maintain data integrity and accessibility."""
        
        test_file.write_text(content)
        print(f"   ✅ Created: {test_file}")
        
        # First server instance - ingest data
        print("\n🔧 Step 2: Server Instance 1 - Ingesting document...")
        server1 = RAGServer(
            persist_directory=temp_dir,
            collection_name="manual_test_5"
        )
        
        result = await server1.ingest_documents([str(test_file)])
        
        if not result["success"]:
            print(f"   ❌ Ingestion failed: {result.get('message', 'Unknown error')}")
            return
        
        chunks_ingested = result["chunks_ingested"]
        stats1 = server1.get_stats()
        print(f"   ✅ Ingested {chunks_ingested} chunks")
        print(f"   Collection stats: {stats1['total_chunks']} total chunks")
        
        # Test retrieval before "reboot"
        print("\n🔍 Step 3: Testing retrieval before 'reboot'...")
        chunks_before = await server1.retrieve_context("persistence test", top_k=3)
        print(f"   ✅ Retrieved {len(chunks_before)} chunks")
        
        # Simulate "reboot" - close server1, create new server2 with same directory
        print("\n🔄 Step 4: Simulating reboot (closing server, creating new instance)...")
        del server1
        
        # Wait a moment to ensure cleanup
        await asyncio.sleep(0.5)
        
        # Second server instance - should see same data
        print("\n🔧 Step 5: Server Instance 2 - Opening same collection...")
        server2 = RAGServer(
            persist_directory=temp_dir,
            collection_name="manual_test_5"
        )
        
        stats2 = server2.get_stats()
        print(f"   Collection stats: {stats2['total_chunks']} total chunks")
        
        if stats2["total_chunks"] != stats1["total_chunks"]:
            print(f"   ❌ Persistence failed: {stats1['total_chunks']} chunks before, {stats2['total_chunks']} chunks after")
            return
        
        print(f"   ✅ Chunk count matches: {stats2['total_chunks']} chunks")
        
        # Verify we can retrieve data
        print("\n🔍 Step 6: Testing retrieval after 'reboot'...")
        chunks_after = await server2.retrieve_context("persistence test", top_k=3)
        
        if not chunks_after:
            print(f"   ❌ Cannot retrieve data after persistence check")
            return
        
        print(f"   ✅ Retrieved {len(chunks_after)} chunks")
        
        # Verify content is correct
        found_persistence = False
        for chunk in chunks_after:
            if "persistence" in chunk["text"].lower():
                found_persistence = True
                break
        
        if not found_persistence:
            print(f"   ⚠️  Retrieved chunks may not match expected content")
        else:
            print(f"   ✅ Content verified: found 'persistence' in retrieved chunks")
        
        # Summary
        print("\n" + "="*60)
        print("✅ TEST 5 PASSED: Persistence check successful")
        print(f"   Data persisted: {stats2['total_chunks']} chunks survived 'reboot'")
        print(f"   Retrieval working: {len(chunks_after)} chunks retrieved")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

