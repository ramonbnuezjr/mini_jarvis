#!/usr/bin/env python3
"""Cleanup script for expired ephemeral documents in RAG memory."""

import asyncio
import logging
import sys
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


async def main():
    """Clean up expired ephemeral documents."""
    print("🧹 RAG Memory Cleanup - Removing Expired Documents")
    print("=" * 60)
    
    try:
        # Initialize RAG server with tiering enabled
        rag_server = RAGServer(enable_tiering=True)
        
        # Get stats before cleanup
        stats_before = rag_server.get_stats()
        print(f"\n📊 Before cleanup:")
        print(f"   Total chunks: {stats_before['total_chunks']}")
        if stats_before.get('tier_counts'):
            for tier, count in stats_before['tier_counts'].items():
                print(f"   {tier.capitalize()}: {count} chunks")
        
        metadata_stats = stats_before.get('metadata_stats', {})
        expired_count = metadata_stats.get('expired_documents', 0)
        print(f"\n⏰ Expired documents: {expired_count}")
        
        if expired_count == 0:
            print("\n✅ No expired documents to clean up!")
            return
        
        # Perform cleanup
        print("\n🧹 Cleaning up expired documents...")
        result = await rag_server.cleanup_expired()
        
        print(f"\n✅ Cleanup complete:")
        print(f"   Expired documents removed: {result['expired_count']}")
        print(f"   Chunks deleted: {result['chunks_deleted']}")
        
        # Get stats after cleanup
        stats_after = rag_server.get_stats()
        print(f"\n📊 After cleanup:")
        print(f"   Total chunks: {stats_after['total_chunks']}")
        if stats_after.get('tier_counts'):
            for tier, count in stats_after['tier_counts'].items():
                print(f"   {tier.capitalize()}: {count} chunks")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

