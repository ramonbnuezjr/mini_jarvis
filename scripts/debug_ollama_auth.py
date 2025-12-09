#!/usr/bin/env python3
"""Debug Ollama Cloud API authentication."""

import asyncio
import httpx
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def debug_auth():
    api_key = os.getenv("OLLAMA_CLOUD_API_KEY")
    base_url = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://api.ollama.cloud/v1")
    
    print(f"API Key: {api_key[:30]}...{api_key[-10:] if api_key else 'MISSING'}")
    print(f"Base URL: {base_url}\n")
    
    # Test 1: List models (Ollama-native endpoint, no /v1 prefix)
    print("=" * 60)
    print("TEST 1: List Models (GET /v1/models)")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            r = await client.get(
                f"{base_url}/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                print("✅ Models endpoint works")
            else:
                print(f"Response: {r.text[:300]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Chat completions (OpenAI-compatible endpoint with /v1 prefix)
    print("\n" + "=" * 60)
    print("TEST 2: Chat Completions (POST /v1/chat/completions)")
    print("=" * 60)
    
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-oss:120b-cloud",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}\n")
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            r = await client.post(url, json=payload, headers=headers)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text[:500]}")
            
            if r.status_code == 200:
                result = r.json()
                print(f"\n✅ Success! Response: {result.get('choices', [{}])[0].get('message', {}).get('content', '')}")
            elif r.status_code == 401:
                print("\n❌ 401 Unauthorized")
                print("Possible issues:")
                print("  - API key format might be wrong")
                print("  - API key might not have access to this endpoint")
                print("  - Authentication header format might be incorrect")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_auth())

