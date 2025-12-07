#!/usr/bin/env python3
"""Diagnose where RAG ingestion is hanging."""

import asyncio
import sys
import time
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer

async def diagnose():
    print("="*60)
    print("RAG Ingestion Hang Diagnosis")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create small test document
        test_file = Path(temp_dir) / "test.md"
        content = "# Test\nThis is a test document with multiple sections.\n" * 5
        test_file.write_text(content)
        
        print(f"\n1. Creating RAG server...")
        start = time.time()
        rag_server = RAGServer(
            persist_directory=temp_dir,
            collection_name="diagnose_test"
        )
        print(f"   ✅ Server created in {time.time() - start:.2f}s")
        
        print(f"\n2. Testing with chunk_size=150, chunk_overlap=30...")
        print(f"   Document size: {len(content)} chars")
        
        # Test ingestion with timeout at each step
        print(f"\n3. Starting ingestion (5 min timeout)...")
        start = time.time()
        
        try:
            result = await asyncio.wait_for(
                rag_server.ingest_documents(
                    [str(test_file)],
                    chunk_size=150,
                    chunk_overlap=30
                ),
                timeout=300
            )
            elapsed = time.time() - start
            print(f"\n✅ Ingestion completed in {elapsed:.2f}s")
            print(f"   Chunks ingested: {result.get('chunks_ingested', 0)}")
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            print(f"\n❌ Ingestion timed out after {elapsed:.2f}s")
            print(f"   This indicates a hang in the ingestion process")
        except Exception as e:
            elapsed = time.time() - start
            print(f"\n❌ Ingestion failed after {elapsed:.2f}s: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(diagnose())

