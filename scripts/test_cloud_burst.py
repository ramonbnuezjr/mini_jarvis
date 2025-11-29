#!/usr/bin/env python3
"""Test script to verify Cloud Burst (Gemini 2.0 Flash) is working."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.cloud_brain import CloudBrain
from src.brain.orchestrator import Orchestrator
from src.brain.router import InferenceTarget

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_cloud_brain_direct():
    """Test Cloud Brain directly."""
    print("\n" + "="*60)
    print("TEST 1: Direct Cloud Brain Test")
    print("="*60)
    
    try:
        async with CloudBrain() as cloud:
            # Health check
            print("🔍 Checking Gemini API health...")
            is_healthy = await cloud.check_health()
            if is_healthy:
                print("✅ Gemini API is accessible and key is valid!")
            else:
                print("❌ Gemini API health check failed")
                return False
            
            # Test query
            print("\n🤔 Testing with a simple query...")
            response = await cloud.think("What is Python in one sentence?")
            print(f"✅ Response received: {response[:100]}...")
            return True
            
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            print(f"❌ {e}")
            print("   Make sure GEMINI_API_KEY is set in .env file")
        else:
            print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_orchestrator_routing():
    """Test that Orchestrator routes complex queries to cloud."""
    print("\n" + "="*60)
    print("TEST 2: Orchestrator Routing Test")
    print("="*60)
    
    try:
        async with Orchestrator() as orchestrator:
            # Test 1: Simple query (should use local)
            print("\n📝 Test 1: Simple query (should use Local Brain)")
            query1 = "What is Python?"
            response1, target1 = await orchestrator.think(query1)
            status1 = "✅" if target1 == InferenceTarget.LOCAL else "❌"
            print(f"{status1} Query: '{query1}'")
            print(f"   Target: {target1.value} (expected: local)")
            print(f"   Response: {response1[:80]}...")
            
            # Test 2: Complex query (should use cloud)
            print("\n📝 Test 2: Complex query (should use Cloud Burst)")
            query2 = "Analyze and compare the economic impact of AI versus the industrial revolution"
            response2, target2 = await orchestrator.think(query2)
            status2 = "✅" if target2 == InferenceTarget.CLOUD else "❌"
            print(f"{status2} Query: '{query2[:60]}...'")
            print(f"   Target: {target2.value} (expected: cloud)")
            print(f"   Response: {response2[:80]}...")
            
            # Test 3: Tool-requiring query (should use cloud)
            print("\n📝 Test 3: Tool-requiring query (should use Cloud Burst)")
            query3 = "What's the weather today?"
            response3, target3 = await orchestrator.think(query3)
            status3 = "✅" if target3 == InferenceTarget.CLOUD else "❌"
            print(f"{status3} Query: '{query3}'")
            print(f"   Target: {target3.value} (expected: cloud)")
            print(f"   Response: {response3[:80]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Mini-JARVIS: Cloud Burst (Gemini 2.0 Flash) Test Suite")
    print("="*60)
    
    # Test 1: Direct Cloud Brain
    cloud_ok = await test_cloud_brain_direct()
    
    if not cloud_ok:
        print("\n⚠️  Cloud Brain test failed. Skipping orchestrator test.")
        return
    
    # Test 2: Orchestrator routing
    await test_orchestrator_routing()
    
    print("\n" + "="*60)
    print("✅ Cloud Burst tests complete!")
    print("="*60)
    print("\n💡 Tip: Run 'python scripts/chat.py' to try it interactively")
    print("   Complex queries will automatically use Gemini 2.0 Flash (☁️)\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")


