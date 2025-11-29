#!/usr/bin/env python3
"""Test script to verify tool integration with Orchestrator."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.orchestrator import Orchestrator
from src.brain.router import InferenceTarget

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_tool_integration():
    """Test that tools are integrated with Orchestrator."""
    print("\n" + "="*60)
    print("Mini-JARVIS: Tool Integration Test")
    print("="*60)
    
    try:
        async with Orchestrator() as orchestrator:
            # Check tool registry
            tools = orchestrator.tool_registry.list_tools()
            print(f"\n📦 Available tools: {len(tools)}")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description'][:50]}...")
            
            # Test 1: Query that should use tools (weather)
            print("\n" + "="*60)
            print("TEST 1: Weather Query (should use get_weather tool)")
            print("="*60)
            
            query1 = "What's the weather in San Francisco?"
            print(f"Query: {query1}")
            print("Processing...")
            
            try:
                response1, target1, tool_calls1 = await orchestrator.think(query1)
                print(f"\n✅ Response received")
                print(f"   Target: {target1.value}")
                print(f"   Tools used: {len(tool_calls1)}")
                if tool_calls1:
                    for tc in tool_calls1:
                        print(f"     - {tc['tool']} with args: {tc['args']}")
                print(f"   Response: {response1[:200]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            # Test 2: Query that should use tools (time)
            print("\n" + "="*60)
            print("TEST 2: Time Query (should use get_time tool)")
            print("="*60)
            
            query2 = "What time is it?"
            print(f"Query: {query2}")
            print("Processing...")
            
            try:
                response2, target2, tool_calls2 = await orchestrator.think(query2)
                print(f"\n✅ Response received")
                print(f"   Target: {target2.value}")
                print(f"   Tools used: {len(tool_calls2)}")
                if tool_calls2:
                    for tc in tool_calls2:
                        print(f"     - {tc['tool']} with args: {tc['args']}")
                print(f"   Response: {response2[:200]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "="*60)
            print("✅ Tool integration test complete!")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_tool_integration())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")

