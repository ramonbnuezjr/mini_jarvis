#!/usr/bin/env python3
"""Manual Test 4: Large Document → Performance Test

This script tests:
- Performance with larger documents (lightweight version for Pi5)
- Ingestion speed
- Retrieval speed
"""

import asyncio
import sys
import tempfile
import shutil
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer


async def main():
    print("="*60)
    print("Manual Test 4: Large Document → Performance Test")
    print("="*60)
    print("(Lightweight version optimized for Pi5)")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create medium-sized document (lighter than UAT version)
        print("\n📄 Step 1: Creating medium-sized document (~15KB)...")
        test_file = Path(temp_dir) / "medium_document.txt"
        
        # Generate content (smaller than UAT to avoid Pi5 overload)
        sections = []
        for i in range(30):  # Reduced from 100 to 30
            sections.append(f"""
Section {i+1}: Technical Content

This is section {i+1} of a technical document.
It contains detailed information about various topics.
The content is structured to test performance with medium documents.
Each section has multiple paragraphs and sentences.
This helps simulate real-world document sizes without overwhelming the Pi5.
""")
        
        content = "\n".join(sections)
        test_file.write_text(content)
        file_size = test_file.stat().st_size
        print(f"   ✅ Created document: {file_size / 1024:.1f} KB")
        
        # Initialize RAG server
        print("\n🔧 Step 2: Initializing RAG server...")
        rag_server = RAGServer(
            persist_directory=temp_dir,
            collection_name="manual_test_4"
        )
        print("   ✅ RAG server initialized")
        
        # Measure ingestion time
        print("\n⏱️  Step 3: Measuring ingestion performance...")
        start_time = time.time()
        result = await rag_server.ingest_documents([str(test_file)])
        ingestion_time = time.time() - start_time
        
        if not result["success"]:
            print(f"   ❌ Ingestion failed: {result.get('message', 'Unknown error')}")
            return
        
        chunks_ingested = result["chunks_ingested"]
        chunks_per_second = chunks_ingested / ingestion_time if ingestion_time > 0 else 0
        
        print(f"   ✅ Ingested {chunks_ingested} chunks in {ingestion_time:.2f} seconds")
        print(f"   Rate: {chunks_per_second:.1f} chunks/second")
        
        # Performance check
        if ingestion_time > 30:
            print(f"   ⚠️  Ingestion took {ingestion_time:.2f}s (may be slow on Pi5)")
        else:
            print(f"   ✅ Ingestion performance acceptable")
        
        # Measure retrieval time
        print("\n⏱️  Step 4: Measuring retrieval performance...")
        start_time = time.time()
        chunks = await rag_server.retrieve_context("technical content", top_k=5)
        retrieval_time = time.time() - start_time
        
        print(f"   ✅ Retrieved {len(chunks)} chunks in {retrieval_time:.2f} seconds")
        
        if retrieval_time > 3:
            print(f"   ⚠️  Retrieval took {retrieval_time:.2f}s (may be slow)")
        else:
            print(f"   ✅ Retrieval performance acceptable")
        
        # Summary
        print("\n" + "="*60)
        print("✅ TEST 4 PASSED: Performance test completed")
        print(f"   Ingestion: {ingestion_time:.2f}s for {chunks_ingested} chunks")
        print(f"   Retrieval: {retrieval_time:.2f}s for {len(chunks)} chunks")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

