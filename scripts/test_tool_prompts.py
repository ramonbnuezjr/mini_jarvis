#!/usr/bin/env python3
"""Test script with prompts that should trigger tool calls."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.orchestrator import Orchestrator
from src.brain.router import InferenceTarget

# Setup logging (show INFO for router decisions)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


# Test prompts that should trigger tool calls
TEST_PROMPTS = [
    {
        "prompt": "What's the weather in San Francisco?",
        "expected_tool": "get_weather",
        "description": "Weather query - should use get_weather tool"
    },
    {
        "prompt": "What time is it right now?",
        "expected_tool": "get_time",
        "description": "Time query - should use get_time tool"
    },
    {
        "prompt": "Search Wikipedia for information about Python programming language",
        "expected_tool": "search_wikipedia",
        "description": "Wikipedia search - should use search_wikipedia tool"
    },
    {
        "prompt": "Find recent research papers about machine learning on arXiv",
        "expected_tool": "search_arxiv",
        "description": "ArXiv search - should use search_arxiv tool"
    },
    {
        "prompt": "Search the web for the latest news about Raspberry Pi 5",
        "expected_tool": "search_web",
        "description": "Web search - should use search_web tool"
    },
    {
        "prompt": "What are the top tech news stories today?",
        "expected_tool": "get_tech_news",
        "description": "Tech news - should use get_tech_news tool"
    },
    {
        "prompt": "What's the temperature in New York City?",
        "expected_tool": "get_weather",
        "description": "Weather query (temperature) - should use get_weather tool"
    },
    {
        "prompt": "What date is it today?",
        "expected_tool": "get_time",
        "description": "Date query - should use get_time tool"
    }
]


async def test_tool_prompts():
    """Test prompts that should trigger tool calls."""
    print("\n" + "="*70)
    print("Mini-JARVIS: Tool Call Test Prompts")
    print("="*70)
    print(f"\nTesting {len(TEST_PROMPTS)} prompts that should trigger tool calls...\n")
    
    try:
        async with Orchestrator() as orchestrator:
            # Check availability
            if not await orchestrator.local_brain.check_health():
                print("❌ Ollama is not running. Please start it with: ollama serve")
                return
                
            if not orchestrator.cloud_brain:
                print("⚠️  Cloud Brain not available (GEMINI_API_KEY not set)")
                print("   Tool calls require Cloud Brain. Skipping tests.\n")
                return
                
            cloud_ok = await orchestrator.cloud_brain.check_health()
            if not cloud_ok:
                print("⚠️  Cloud Brain API key invalid or unavailable")
                print("   Tool calls require Cloud Brain. Skipping tests.\n")
                return
            
            print("✅ Local Brain: Available")
            print("✅ Cloud Brain: Available\n")
            print("="*70)
            
            results = []
            
            for i, test in enumerate(TEST_PROMPTS, 1):
                print(f"\n[{i}/{len(TEST_PROMPTS)}] {test['description']}")
                print(f"Prompt: \"{test['prompt']}\"")
                print(f"Expected tool: {test['expected_tool']}")
                print("-" * 70)
                
                try:
                    print("Processing...", end="", flush=True)
                    response, target, tool_calls = await orchestrator.think(test['prompt'])
                    print("\r" + " " * 20 + "\r", end="")  # Clear line
                    
                    # Check results
                    tools_used = [tc["tool"] for tc in tool_calls]
                    expected_found = test['expected_tool'] in tools_used
                    
                    if expected_found:
                        print(f"✅ PASS: Tool '{test['expected_tool']}' was called")
                    else:
                        print(f"⚠️  WARNING: Expected '{test['expected_tool']}' but got: {tools_used}")
                    
                    if tool_calls:
                        print(f"   Tools used: {', '.join(tools_used)}")
                    else:
                        print(f"   ⚠️  No tools were called (query may have been answered without tools)")
                    
                    print(f"   Target: {target.value}")
                    print(f"   Response preview: {response[:150]}...")
                    
                    results.append({
                        "test": test,
                        "passed": expected_found,
                        "tools_used": tools_used,
                        "target": target
                    })
                    
                except Exception as e:
                    print(f"\r❌ ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    results.append({
                        "test": test,
                        "passed": False,
                        "error": str(e)
                    })
            
            # Summary
            print("\n" + "="*70)
            print("TEST SUMMARY")
            print("="*70)
            
            passed = sum(1 for r in results if r.get("passed", False))
            total = len(results)
            
            print(f"\nTotal tests: {total}")
            print(f"Passed: {passed}")
            print(f"Failed/Warnings: {total - passed}")
            
            if passed == total:
                print("\n✅ All tests passed!")
            else:
                print("\n⚠️  Some tests had issues. Check logs above.")
            
            print("\n" + "="*70)
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_tool_prompts())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")

