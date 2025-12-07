"""Test script for RAG pipeline."""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.rag_server import RAGServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rag():
    """Test RAG retrieval."""
    # Initialize RAG server
    rag_server = RAGServer()
    
    # Check if we have any documents
    stats = rag_server.get_stats()
    logger.info(f"RAG Stats: {stats}")
    
    if stats["total_chunks"] == 0:
        logger.warning("No documents in memory. Ingest some documents first:")
        logger.warning("  python scripts/ingest_documents.py <file1> <file2> ...")
        return
    
    # Test queries
    test_queries = [
        "What is the main topic?",
        "Summarize the key points",
        "What are the important details?"
    ]
    
    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*60}")
        
        chunks = await rag_server.retrieve_context(query, top_k=3)
        
        if chunks:
            logger.info(f"Retrieved {len(chunks)} chunks:")
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"\n--- Chunk {i} (Score: {chunk['score']:.3f}) ---")
                logger.info(f"Source: {chunk['metadata'].get('source', 'unknown')}")
                logger.info(f"Text: {chunk['text'][:200]}...")
        else:
            logger.warning("No relevant chunks found")


if __name__ == "__main__":
    asyncio.run(test_rag())

