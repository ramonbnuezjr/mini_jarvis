#!/usr/bin/env python3
"""Test script for tiered memory system."""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.rag_server import RAGServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_tiered_memory():
    """Test tiered memory ingestion and retrieval."""
    print("🧪 Testing Tiered Memory System")
    print("=" * 60)
    
    # Create temporary test documents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test documents for each tier
        core_doc = temp_path / "core_doc.txt"
        core_doc.write_text("This is a core document about artificial intelligence and machine learning. "
                           "It contains important information that should be prioritized in retrieval.")
        
        reference_doc = temp_path / "reference_doc.txt"
        reference_doc.write_text("This is a reference document about Python programming. "
                                "It contains standard information that should be retrieved normally.")
        
        ephemeral_doc = temp_path / "ephemeral_doc.txt"
        ephemeral_doc.write_text("This is an ephemeral document about temporary notes. "
                                "It should be deprioritized in retrieval and can expire.")
        
        print("\n📝 Created test documents:")
        print(f"   Core: {core_doc.name}")
        print(f"   Reference: {reference_doc.name}")
        print(f"   Ephemeral: {ephemeral_doc.name}")
        
        # Initialize RAG server with tiering enabled
        print("\n🔧 Initializing RAG Server with tiering...")
        rag_server = RAGServer(enable_tiering=True)
        
        # Ingest documents into different tiers
        print("\n📥 Ingesting documents into tiers...")
        
        # Core tier
        result = await rag_server.ingest_documents(
            [str(core_doc)],
            tier="core",
            chunk_size=200,
            chunk_overlap=50
        )
        print(f"   ✅ Core: {result['chunks_ingested']} chunks")
        
        # Reference tier
        result = await rag_server.ingest_documents(
            [str(reference_doc)],
            tier="reference",
            chunk_size=200,
            chunk_overlap=50
        )
        print(f"   ✅ Reference: {result['chunks_ingested']} chunks")
        
        # Ephemeral tier (with TTL)
        result = await rag_server.ingest_documents(
            [str(ephemeral_doc)],
            tier="ephemeral",
            ttl_seconds=3600,  # 1 hour TTL
            chunk_size=200,
            chunk_overlap=50
        )
        print(f"   ✅ Ephemeral: {result['chunks_ingested']} chunks (TTL: 1 hour)")
        
        # Get stats
        stats = rag_server.get_stats()
        print(f"\n📊 Memory Stats:")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Tier counts: {stats['tier_counts']}")
        
        # Test retrieval with weighted scoring
        print("\n🔍 Testing weighted retrieval...")
        query = "artificial intelligence"
        chunks = await rag_server.retrieve_context(query, top_k=5, min_score=0.0)
        
        print(f"\n📋 Retrieved {len(chunks)} chunks for query: '{query}'")
        for i, chunk in enumerate(chunks, 1):
            tier = chunk.get('tier', 'unknown')
            score = chunk.get('score', 0.0)
            base_score = chunk.get('base_score', 0.0)
            weight = chunk.get('weight', 1.0)
            print(f"\n   Chunk {i} (Tier: {tier}, Weight: {weight}x):")
            print(f"      Base Score: {base_score:.3f}")
            print(f"      Weighted Score: {score:.3f}")
            print(f"      Text: {chunk['text'][:100]}...")
        
        # Verify core documents are boosted
        core_chunks = [c for c in chunks if c.get('tier') == 'core']
        if core_chunks:
            print(f"\n✅ Core documents retrieved: {len(core_chunks)}")
            print(f"   Core chunks have 1.5x weight boost")
        else:
            print("\n⚠️  No core documents in top results")
        
        # Test cleanup (should not expire anything yet)
        print("\n🧹 Testing cleanup (should find no expired documents)...")
        cleanup_result = await rag_server.cleanup_expired()
        print(f"   {cleanup_result['message']}")
        
        print("\n✅ Tiered memory test complete!")


if __name__ == "__main__":
    asyncio.run(test_tiered_memory())

