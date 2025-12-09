#!/usr/bin/env python3
"""Simple interactive chat interface for Mini-JARVIS."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.orchestrator import Orchestrator
from src.brain.router import InferenceTarget

# Optional RAG import
try:
    from src.memory.rag_server import RAGServer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    RAGServer = None

# Setup logging (less verbose for interactive use)
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors
    format='%(levelname)s: %(message)s'
)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


async def chat_loop():
    """Interactive chat loop with JARVIS."""
    print("\n" + "="*60)
    print("Mini-JARVIS - Interactive Chat")
    print("="*60)
    print("Ask me anything! (Type 'quit' or 'exit' to end)\n")
    
    # Initialize RAG server if available (with tiering enabled)
    rag_server = None
    if RAG_AVAILABLE:
        try:
            # Enable tiered memory (Phase 4.5)
            rag_server = RAGServer(enable_tiering=True)
            stats = rag_server.get_stats()
            if stats.get("tiering_enabled"):
                tier_counts = stats.get("tier_counts", {})
                total = stats["total_chunks"]
                if total > 0:
                    tier_info = ", ".join([f"{k}: {v}" for k, v in tier_counts.items() if v > 0])
                    print(f"📚 RAG Memory (Tiered): {total} chunks ({tier_info})\n")
                else:
                    print("📚 RAG Memory (Tiered): Available (no documents ingested yet)\n")
            else:
                if stats["total_chunks"] > 0:
                    print(f"📚 RAG Memory: {stats['total_chunks']} chunks loaded\n")
                else:
                    print("📚 RAG Memory: Available (no documents ingested yet)\n")
        except Exception as e:
            print(f"⚠️  RAG Memory: Not available ({e})\n")
            rag_server = None
    
    async with Orchestrator(rag_server=rag_server) as orchestrator:
        # Check local brain health
        if not await orchestrator.local_brain.check_health():
            print("❌ Ollama is not running. Please start it with: ollama serve")
            return
            
        # Check cloud brain availability
        if orchestrator.cloud_brain:
            cloud_ok = await orchestrator.cloud_brain.check_health()
            if cloud_ok:
                print(f"✅ Cloud Burst ({orchestrator.cloud_model}) available\n")
            else:
                print(f"⚠️  Cloud Burst ({orchestrator.cloud_model}) API key invalid or unavailable\n")
        else:
            print("⚠️  Cloud Burst not configured (OLLAMA_CLOUD_API_KEY not set)\n")
        
        while True:
            try:
                # Get user input
                question = input("You: ").strip()
                
                if not question:
                    continue
                    
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                # Get response from orchestrator
                print("🤔 Thinking...", end="", flush=True)
                response, target, tool_calls = await orchestrator.think(question)
                print("\r" + " "*20 + "\r", end="")  # Clear "Thinking..." line
                
                # Show which brain was used
                brain_indicator = "☁️" if target == InferenceTarget.CLOUD else "🏠"
                
                # Show tool usage if any
                if tool_calls:
                    tools_used = ", ".join([tc.get("tool") or tc.get("name", "unknown") for tc in tool_calls])
                    print(f"🔧 Tools used: {tools_used}")
                
                print(f"JARVIS {brain_indicator}: {response}\n")
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

