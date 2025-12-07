#!/usr/bin/env python3
"""Test retrieval from Google Drive synced documents."""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def test_retrieval():
    """Test retrieval with queries about synced documents."""
    print("="*70)
    print("Testing RAG Retrieval from Google Drive Synced Documents")
    print("="*70)
    
    # Initialize RAG server with tiering
    rag_server = RAGServer(enable_tiering=True)
    
    # Show stats
    stats = rag_server.get_stats()
    print(f"\n📊 RAG Memory Stats:")
    print(f"   Total chunks: {stats['total_chunks']}")
    if stats.get('tiering_enabled'):
        tier_counts = stats.get('tier_counts', {})
        print(f"   Tier distribution:")
        for tier, count in tier_counts.items():
            print(f"      {tier}: {count} chunks")
    print()
    
    # Test queries based on synced documents
    test_queries = [
        # Core document query
        "What is the Pironman5 MAX?",
        
        # Edge computing queries (from reference papers)
        "What is edge computing?",
        "What are the challenges in edge AI?",
        "How does federated learning work in edge computing?",
        
        # Thermodynamic computing queries (from reference papers)
        "What is thermodynamic computing?",
        "How does thermodynamic computing work?",
        
        # AI/ML queries (from McKinsey paper)
        "What are the latest trends in AI agents?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("\n" + "="*70)
        print(f"Query {i}/{len(test_queries)}: {query}")
        print("="*70)
        
        try:
            # Retrieve context
            chunks = await rag_server.retrieve_context(query, top_k=3, min_score=0.3)
            
            if chunks:
                print(f"\n✅ Retrieved {len(chunks)} relevant chunk(s):\n")
                
                for j, chunk in enumerate(chunks, 1):
                    score = chunk.get('score', 0.0)
                    metadata = chunk.get('metadata', {})
                    text = chunk.get('text', '')
                    
                    # Extract source info
                    source = metadata.get('file_path', 'Unknown')
                    tier = metadata.get('tier', 'unknown')
                    folder = metadata.get('source', {}).get('folder', 'Unknown') if isinstance(metadata.get('source'), dict) else 'Unknown'
                    
                    print(f"--- Chunk {j} (Score: {score:.3f}, Tier: {tier}) ---")
                    if folder != 'Unknown':
                        print(f"Source: {folder} → {Path(source).name}")
                    else:
                        print(f"Source: {Path(source).name}")
                    print(f"Text: {text[:300]}...")
                    if len(text) > 300:
                        print(f"      ({len(text)} characters total)")
                    print()
            else:
                print(f"\n⚠️  No relevant chunks found (min_score=0.3)")
        
        except Exception as e:
            logger.error(f"Error retrieving context for query '{query}': {e}")
            print(f"\n❌ Error: {e}")
    
    print("\n" + "="*70)
    print("Retrieval Test Complete")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_retrieval())

