#!/usr/bin/env python3
"""Test tools through the full orchestrator flow."""

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

async def test_tools():
    """Test tools through orchestrator."""
    test_prompts = [
        "Look up Albert Einstein on Wikipedia",
        "Find recent research papers about machine learning on arXiv",
        "Search the web for the latest news about Raspberry Pi 5",
    ]
    
    async with Orchestrator() as orchestrator:
        for prompt in test_prompts:
            print(f"\n{'='*60}")
            print(f"Testing: {prompt}")
            print('='*60)
            
            try:
                response, target, tool_calls = await orchestrator.think(prompt)
                
                print(f"\nTarget: {target}")
                print(f"Tool calls: {tool_calls}")
                print(f"\nResponse:\n{response}\n")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tools())

