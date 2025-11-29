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
    
    async with Orchestrator() as orchestrator:
        # Check local brain health
        if not await orchestrator.local_brain.check_health():
            print("❌ Ollama is not running. Please start it with: ollama serve")
            return
            
        # Check cloud brain availability
        if orchestrator.cloud_brain:
            cloud_ok = await orchestrator.cloud_brain.check_health()
            if cloud_ok:
                print("✅ Cloud Burst (Gemini 2.0 Flash) available\n")
            else:
                print("⚠️  Cloud Burst (Gemini 2.0 Flash) API key invalid or unavailable\n")
        else:
            print("⚠️  Cloud Burst not configured (GEMINI_API_KEY not set)\n")
        
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
                    tools_used = ", ".join([tc["tool"] for tc in tool_calls])
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

