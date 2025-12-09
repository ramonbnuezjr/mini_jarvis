#!/usr/bin/env python3
"""Test the hybrid Ollama pattern: local gateway with cloud models."""

import asyncio
import httpx
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def test_hybrid_setup():
    """Test local Ollama gateway with cloud model."""
    base_url = "http://localhost:11434"
    model = "gpt-oss:120b-cloud"
    
    print("=" * 60)
    print("Testing Hybrid Ollama Pattern")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()
    
    # Test 1: Check if Ollama is running
    print("Test 1: Check if local Ollama is running...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{base_url}/api/tags")
            if r.status_code == 200:
                print("✅ Local Ollama is running")
            else:
                print(f"❌ Ollama returned status {r.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False
    
    # Test 2: Check if cloud model is available
    print("\nTest 2: Check if cloud model is available...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{base_url}/api/tags")
            models = r.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if model in model_names:
                print(f"✅ Model '{model}' is available")
            else:
                print(f"⚠️  Model '{model}' not found in local models")
                print(f"   Available models: {', '.join(model_names[:5])}")
                print(f"   Run: ollama pull {model}")
                return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False
    
    # Test 3: Test chat completion with cloud model
    print("\nTest 3: Test chat completion with cloud model...")
    url = f"{base_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "max_tokens": 5
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, json=payload, headers=headers)
            
            if r.status_code == 200:
                result = r.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"✅ Chat completion successful!")
                print(f"   Response: {content}")
                return True
            elif r.status_code == 401:
                print("❌ 401 Unauthorized")
                print("   Run: ollama signin")
                return False
            elif r.status_code == 404:
                print(f"❌ 404 Model not found")
                print(f"   Run: ollama pull {model}")
                return False
            else:
                print(f"❌ Error {r.status_code}: {r.text[:200]}")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_hybrid_setup())
    if success:
        print("\n" + "=" * 60)
        print("✅ All tests passed! Hybrid setup is working.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Setup incomplete. Please follow the instructions above.")
        print("=" * 60)
    sys.exit(0 if success else 1)

