#!/usr/bin/env python3
"""Simple test to verify chunking works with different chunk counts."""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer

async def test_chunking(chunk_count_name, content, chunk_size, chunk_overlap):
    print(f"\n{'='*60}")
    print(f"Testing: {chunk_count_name} chunks")
    print(f"Document size: {len(content)} chars")
    print(f"Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
    print(f"{'='*60}")
    
    temp_dir = tempfile.mkdtemp()
    try:
        test_file = Path(temp_dir) / "test.md"
        test_file.write_text(content)
        
        rag_server = RAGServer(
            persist_directory=temp_dir,
            collection_name=f"test_{chunk_count_name}"
        )
        
        print("Starting ingestion...")
        import time
        start = time.time()
        
        try:
            result = await asyncio.wait_for(
                rag_server.ingest_documents(
                    [str(test_file)],
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                ),
                timeout=120
            )
            elapsed = time.time() - start
            print(f"✅ Success! Completed in {elapsed:.2f}s")
            print(f"   Chunks ingested: {result.get('chunks_ingested', 0)}")
            return True
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            print(f"❌ Timed out after {elapsed:.2f}s")
            return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

async def main():
    # Test 1: 3 chunks (like diagnostic)
    content1 = "# Test\nThis is a test document.\n" * 10
    await test_chunking("3", content1, 150, 30)
    
    # Test 2: 5 chunks
    content2 = "# Test\nThis is a test document with more content.\n" * 15
    await test_chunking("5", content2, 150, 30)
    
    # Test 3: 7 chunks (like the actual test)
    content3 = """# Technical Documentation

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
    await test_chunking("7", content3, 150, 30)

if __name__ == "__main__":
    asyncio.run(main())

