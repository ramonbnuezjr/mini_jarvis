#!/usr/bin/env python3
"""Test script for Local Brain (Ollama) connectivity and inference."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.local_brain import LocalBrain
from src.brain.router import Router, InferenceTarget

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_health_check():
    """Test Ollama health check."""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    async with LocalBrain() as brain:
        is_healthy = await brain.check_health()
        if is_healthy:
            print("✅ Ollama is running and accessible")
        else:
            print("❌ Ollama is not accessible. Make sure it's running:")
            print("   $ ollama serve")
            return False
            
        # List available models
        models = await brain.list_models()
        print(f"\n📦 Available models: {models if models else 'None found'}")
        return True


async def test_simple_query():
    """Test simple query to local brain."""
    print("\n" + "="*60)
    print("TEST 2: Simple Query")
    print("="*60)
    
    async with LocalBrain() as brain:
        prompt = "What is Python in one sentence?"
        print(f"🤔 Asking: {prompt}")
        
        try:
            response = await brain.think(prompt)
            print(f"🧠 Response: {response}")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_router():
    """Test routing logic."""
    print("\n" + "="*60)
    print("TEST 3: Router Logic")
    print("="*60)
    
    router = Router(prefer_local=True)
    
    test_cases = [
        ("What is Python?", 0, None, InferenceTarget.LOCAL),
        ("Summarize and compare Python vs JavaScript in detail", 0, None, InferenceTarget.CLOUD),
        ("Write a Python function to sort a list", 0, "code", InferenceTarget.LOCAL),
        ("Analyze the economic impact of AI", 5000, None, InferenceTarget.CLOUD),
        ("Analyze this complex medical report", 0, None, InferenceTarget.CLOUD),  # Should burst to cloud
    ]
    
    for query, context_size, task_hint, expected in test_cases:
        result = router.route(query, context_size, task_hint)
        status = "✅" if result == expected else "❌"
        print(f"{status} Query: '{query[:50]}...'")
        print(f"   Context: {context_size} tokens, Hint: {task_hint}")
        print(f"   Routed to: {result.value} (expected: {expected.value})")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Mini-JARVIS: Local Brain Test Suite")
    print("="*60)
    
    # Test 1: Health check
    health_ok = await test_health_check()
    if not health_ok:
        print("\n⚠️  Skipping further tests. Please start Ollama first.")
        return
        
    # Test 2: Simple query
    await test_simple_query()
    
    # Test 3: Router
    await test_router()
    
    print("\n" + "="*60)
    print("✅ Tests complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

