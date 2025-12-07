#!/usr/bin/env python3
"""Quick test of chat with RAG - single query."""

import asyncio
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.brain.orchestrator import Orchestrator
from src.memory.rag_server import RAGServer

logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def quick_test():
    """Quick test with one query."""
    print("="*70)
    print("Quick RAG Chat Test")
    print("="*70)
    
    # Initialize RAG
    rag_server = RAGServer(enable_tiering=True)
    stats = rag_server.get_stats()
    print(f"\n📚 RAG Memory: {stats['total_chunks']} chunks loaded")
    
    # Test one query
    query = "What is the Pironman5 MAX? Tell me about its key features."
    
    async with Orchestrator(rag_server=rag_server, use_rag=True) as orchestrator:
        if not await orchestrator.local_brain.check_health():
            print("❌ Ollama not running")
            return
        
        print(f"\n❓ Query: {query}")
        print("🤔 Processing...")
        
        response, target, tool_calls = await orchestrator.think(query, use_rag_context=True)
        
        brain = "☁️ Cloud" if target.value == "cloud" else "🏠 Local"
        print(f"\n{brain} Response:")
        print("-" * 70)
        print(response)
        print("-" * 70)
        
        if tool_calls:
            print(f"\n🔧 Tools used: {len(tool_calls)}")


if __name__ == "__main__":
    asyncio.run(quick_test())

