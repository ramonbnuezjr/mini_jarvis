#!/usr/bin/env python3
"""Simple interactive chat interface for Mini-JARVIS."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.local_brain import LocalBrain
from src.brain.router import Router, InferenceTarget

# Setup logging (less verbose for interactive use)
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors
    format='%(levelname)s: %(message)s'
)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


async def chat_loop():
    """Interactive chat loop with JARVIS."""
    router = Router(prefer_local=True)
    
    print("\n" + "="*60)
    print("Mini-JARVIS - Interactive Chat")
    print("="*60)
    print("Ask me anything! (Type 'quit' or 'exit' to end)\n")
    
    async with LocalBrain() as brain:
        # Check health first
        if not await brain.check_health():
            print("❌ Ollama is not running. Please start it with: ollama serve")
            return
        
        while True:
            try:
                # Get user input
                question = input("You: ").strip()
                
                if not question:
                    continue
                    
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                # Route the query
                target = router.route(question)
                
                if target == InferenceTarget.CLOUD:
                    # Check if it's a tool-requiring query
                    tool_keywords = ["weather", "temperature", "forecast", "calendar", "schedule", 
                                   "time", "date", "today", "control", "turn on", "turn off"]
                    is_tool_query = any(keyword in question.lower() for keyword in tool_keywords)
                    
                    if is_tool_query:
                        print("🔧 [Router: This query requires tools/APIs (Weather, Calendar, etc.)]")
                        print("   Tools/MCP Server not implemented yet. Cloud Burst would help,")
                        print("   but tools are needed for real-time data. Falling back to local...\n")
                    else:
                        print("🧠 [Router: This query should use Cloud Burst, but it's not implemented yet]")
                        print("   Falling back to local Llama 3.2 3B...\n")
                
                # Get response from local brain
                print("🤔 Thinking...", end="", flush=True)
                response = await brain.think(question)
                print("\r" + " "*20 + "\r", end="")  # Clear "Thinking..." line
                
                print(f"JARVIS: {response}\n")
                
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

