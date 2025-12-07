#!/usr/bin/env python3
"""Debug script to find where RAG ingestion hangs."""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer
from src.memory.document_ingester import DocumentIngester

async def test():
    print("Step 1: Creating test file...")
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "test.md"
    test_file.write_text("# Test\nThis is a test document.")
    print(f"   Created: {test_file}")
    sys.stdout.flush()
    
    print("\nStep 2: Initializing RAG server...")
    sys.stdout.flush()
    rag_server = RAGServer(
        persist_directory=temp_dir,
        collection_name="debug_test"
    )
    print("   RAG server initialized")
    sys.stdout.flush()
    
    print("\nStep 3: Testing DocumentIngester directly...")
    sys.stdout.flush()
    ingester = DocumentIngester()
    print("   Ingester created")
    sys.stdout.flush()
    
    print("\nStep 4: Calling ingest_file...")
    sys.stdout.flush()
    try:
        chunks, metadatas = await ingester.ingest_file(str(test_file), chunk_size=150, chunk_overlap=30)
        print(f"   Success! Got {len(chunks)} chunks")
        sys.stdout.flush()
    except Exception as e:
        print(f"   Error in ingest_file: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return
    
    print("\nStep 5: Testing embed_chunks...")
    sys.stdout.flush()
    try:
        embeddings = await ingester.embed_chunks(chunks)
        print(f"   Success! Got {len(embeddings)} embeddings")
        sys.stdout.flush()
    except Exception as e:
        print(f"   Error in embed_chunks: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return
    
    print("\nStep 6: Calling rag_server.ingest_documents...")
    sys.stdout.flush()
    try:
        result = await rag_server.ingest_documents([str(test_file)], chunk_size=150, chunk_overlap=30)
        print(f"   Success! Result: {result}")
        sys.stdout.flush()
    except Exception as e:
        print(f"   Error in ingest_documents: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(test())

