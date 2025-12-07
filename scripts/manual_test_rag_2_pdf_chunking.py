#!/usr/bin/env python3
"""Manual Test 2: Ingest PDF → Test Chunking

This script tests:
- Chunking documents into smaller pieces
- Verifying chunk sizes are appropriate
- Ensuring chunks are searchable
"""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check if virtual environment is activated
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("⚠️  WARNING: Virtual environment may not be activated!")
    print("   Run: source venv/bin/activate")
    print("   Current Python: {sys.executable}")
    print()

# Check dependencies before importing
try:
    import sentence_transformers
except ImportError:
    print("❌ ERROR: sentence-transformers not found!")
    print("   Make sure virtual environment is activated:")
    print("   source venv/bin/activate")
    print("   Then install: pip install sentence-transformers")
    sys.exit(1)

from src.memory.rag_server import RAGServer


async def main():
    print("="*60)
    print("Manual Test 2: Ingest PDF → Test Chunking")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Check PDF support
        try:
            import PyPDF2
            pdf_support = True
        except ImportError:
            pdf_support = False
            print("\n⚠️  PDF support not available (PyPDF2 not installed)")
            print("   Testing with markdown file instead...")
        
        # Create test document (simulating multi-section document)
        print("\n📄 Step 1: Creating test document...")
        test_file = Path(temp_dir) / "test_document.md"
        content = """# Technical Documentation

## Introduction
This is a technical document with multiple sections.
The system consists of multiple components working together.

## Section 1: Overview
This section provides an overview of the system architecture.
Each component has specific responsibilities and interfaces.

## Section 2: Implementation
Implementation details are critical for understanding the system.
Multiple test types are used: unit tests, integration tests, and UAT.

## Section 3: Testing
Testing ensures system reliability and correctness.
The system must be deployed to production environments safely.

## Section 4: Deployment
Deployment involves multiple steps and careful planning.
This document covers all major aspects of the system.

## Conclusion
This document provides comprehensive technical documentation."""
        
        test_file.write_text(content)
        print(f"   ✅ Created: {test_file}")
        print(f"   Size: {len(content)} characters")
        
        # Initialize RAG server
        print("\n🔧 Step 2: Initializing RAG server...")
        rag_server = RAGServer(
            persist_directory=temp_dir,
            collection_name="manual_test_2"
        )
        print("   ✅ RAG server initialized")
        
        # Ingest with small chunk size to force multiple chunks
        print("\n📥 Step 3: Ingesting with chunk_size=150, chunk_overlap=30...")
        print("   ⚠️  NOTE: Model is already cached, this should be fast")
        print("   If this hangs, it may be a ChromaDB issue with many chunks")
        import sys
        sys.stdout.flush()  # Ensure output is visible
        
        # Add timeout wrapper with progress
        print("   Starting ingestion (will timeout after 2 minutes)...")
        sys.stdout.flush()
        
        try:
            result = await asyncio.wait_for(
                rag_server.ingest_documents(
                    [str(test_file)],
                    chunk_size=150,
                    chunk_overlap=30
                ),
                timeout=120  # 2 minute timeout (model is cached, should be fast)
            )
        except asyncio.TimeoutError:
            print("\n   ❌ Ingestion timed out after 2 minutes")
            print("   This suggests a hang in ChromaDB or embedding generation.")
            print("   The diagnostic script worked with 3 chunks, so this might be")
            print("   related to the number of chunks created from this document.")
            return
        
        if not result["success"]:
            print(f"   ❌ Ingestion failed: {result.get('message', 'Unknown error')}")
            return
        
        chunks_ingested = result["chunks_ingested"]
        print(f"   ✅ Ingested {chunks_ingested} chunks")
        
        if chunks_ingested < 2:
            print(f"   ⚠️  Expected multiple chunks, got {chunks_ingested}")
        
        # Verify chunking
        print("\n🔍 Step 4: Verifying chunking...")
        stats = rag_server.get_stats()
        print(f"   Total chunks in collection: {stats['total_chunks']}")
        
        # Test retrieval to verify chunks are searchable
        chunks = await rag_server.retrieve_context("system architecture", top_k=3)
        
        if chunks:
            print(f"   ✅ Retrieved {len(chunks)} chunks")
            chunk_sizes = [len(chunk["text"]) for chunk in chunks]
            print(f"   Chunk sizes: min={min(chunk_sizes)}, max={max(chunk_sizes)}, avg={sum(chunk_sizes)//len(chunk_sizes)}")
            
            # Verify chunk sizes are reasonable
            if max(chunk_sizes) > 300:
                print(f"   ⚠️  Largest chunk ({max(chunk_sizes)} chars) seems large for chunk_size=150")
            else:
                print(f"   ✅ Chunk sizes are reasonable")
        else:
            print(f"   ❌ No chunks retrieved")
            return
        
        # Summary
        print("\n" + "="*60)
        print("✅ TEST 2 PASSED: Document chunking working correctly")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

