#!/usr/bin/env python3
"""Test a specific query with JARVIS."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.orchestrator import Orchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


async def test_query(query: str):
    """Test a specific query."""
    print("\n" + "="*60)
    print("Mini-JARVIS - Testing Query")
    print("="*60)
    print(f"\nQuery: {query}\n")
    
    async with Orchestrator() as orchestrator:
        # Check local brain health
        if not await orchestrator.local_brain.check_health():
            print("❌ Ollama is not running. Please start it with: ollama serve")
            return
            
        # Check cloud brain availability
        if orchestrator.cloud_brain:
            cloud_ok = await orchestrator.cloud_brain.check_health()
            if cloud_ok:
                print("✅ Cloud Burst (Gemini 2.0 Flash) available")
            else:
                print("⚠️  Cloud Burst (Gemini 2.0 Flash) API key invalid or unavailable")
        else:
            print("⚠️  Cloud Burst not configured (OLLAMA_CLOUD_API_KEY not set)")
        
        print("\n" + "-"*60)
        print("Processing query...\n")
        
        # Get response
        response, target_used, tool_calls = await orchestrator.think(query)
        
        # Display results
        print("="*60)
        if target_used.value == "LOCAL":
            print("🏠 Using: Local Brain (Llama 3.2 3B)")
        else:
            print("☁️  Using: Cloud Burst (Gemini 2.0 Flash)")
        
        if tool_calls:
            print(f"\n🔧 Tools used: {', '.join([tc.get('name', 'unknown') for tc in tool_calls])}")
        
        print("\n" + "-"*60)
        print("Response:")
        print("-"*60)
        print(response)
        print("="*60 + "\n")


if __name__ == "__main__":
    # Default query if none provided
    query = "What time is it and what is the weather like in NYC today?"
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    
    asyncio.run(test_query(query))

