#!/usr/bin/env python3
"""Non-interactive test of chat interface with RAG integration."""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.brain.orchestrator import Orchestrator
from src.memory.rag_server import RAGServer

# Setup logging (less verbose)
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def test_chat_with_rag():
    """Test chat interface with RAG integration."""
    print("="*70)
    print("Testing Chat Interface with RAG Integration")
    print("="*70)
    
    # Initialize RAG server with tiering
    print("\n📚 Initializing RAG server...")
    rag_server = RAGServer(enable_tiering=True)
    stats = rag_server.get_stats()
    
    if stats.get("tiering_enabled"):
        tier_counts = stats.get("tier_counts", {})
        total = stats["total_chunks"]
        tier_info = ", ".join([f"{k}: {v}" for k, v in tier_counts.items() if v > 0])
        print(f"   ✅ RAG Memory (Tiered): {total} chunks ({tier_info})")
    else:
        print(f"   ✅ RAG Memory: {stats['total_chunks']} chunks")
    
    # Test queries that should use RAG context
    test_queries = [
        "What is the Pironman5 MAX?",
        "Tell me about edge computing.",
        "What are the challenges in edge AI?",
        "Explain thermodynamic computing.",
    ]
    
    async with Orchestrator(rag_server=rag_server, use_rag=True) as orchestrator:
        # Check local brain health
        if not await orchestrator.local_brain.check_health():
            print("\n❌ Ollama is not running. Please start it with: ollama serve")
            return
        
        # Check cloud brain availability
        cloud_available = False
        if orchestrator.cloud_brain:
            cloud_available = await orchestrator.cloud_brain.check_health()
            if cloud_available:
                print("   ✅ Cloud Burst (Gemini 2.0 Flash) available")
            else:
                print("   ⚠️  Cloud Burst (Gemini 2.0 Flash) API key invalid or unavailable")
        else:
            print("   ⚠️  Cloud Burst not configured (OLLAMA_CLOUD_API_KEY not set)")
        
        print("\n" + "="*70)
        print("Testing Queries with RAG Context")
        print("="*70)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*70}")
            print(f"Query {i}/{len(test_queries)}: {query}")
            print("="*70)
            
            try:
                print("🤔 Thinking...", end="", flush=True)
                response, target, tool_calls = await orchestrator.think(query, use_rag_context=True)
                print("\r" + " "*20 + "\r", end="")  # Clear "Thinking..." line
                
                # Show which brain was used
                brain_indicator = "☁️" if target.value == "cloud" else "🏠"
                print(f"\n{brain_indicator} Response ({target.value.upper()}):")
                print("-" * 70)
                print(response)
                print("-" * 70)
                
                if tool_calls:
                    print(f"\n🔧 Tools used: {len(tool_calls)}")
                    for tool_call in tool_calls:
                        print(f"   - {tool_call.get('name', 'unknown')}")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "="*70)
    print("Chat Test Complete")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_chat_with_rag())

