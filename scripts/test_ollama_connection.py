#!/usr/bin/env python3
"""Quick test to verify Ollama Cloud API connection."""

import asyncio
import httpx
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def test_ollama_cloud():
    api_key = os.getenv("OLLAMA_CLOUD_API_KEY")
    base_url = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://api.ollama.cloud/v1")
    model = os.getenv("OLLAMA_CLOUD_MODEL", "gpt-oss:20b-cloud")
    
    if not api_key:
        print("❌ OLLAMA_CLOUD_API_KEY not found in .env")
        return False
    
    if api_key == "your-ollama-cloud-key-here":
        print("❌ Please set your actual Ollama Cloud API key in .env")
        return False
    
    print(f"🔍 Testing Ollama Cloud API...")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print(f"   API Key: {api_key[:20]}...{api_key[-4:]}")
    print()
    
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }
    
    try:
        # Try with SSL verification first
        print("Attempting connection with SSL verification...")
        async with httpx.AsyncClient(verify=True, timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"✅ Success! Response: {content}")
                return True
            elif response.status_code == 401:
                print(f"❌ 401 Unauthorized - API key might be invalid")
                print(f"   Response: {response.text[:200]}")
                return False
            else:
                print(f"❌ Error {response.status_code}: {response.text[:200]}")
                return False
    except Exception as e:
        error_str = str(e).upper()
        if "CERTIFICATE" in error_str or "SSL" in error_str:
            print(f"⚠️  SSL certificate error detected")
            print(f"   Error: {e}")
            print()
            print("Trying without SSL verification (for testing only)...")
            try:
                async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    print(f"✅ Status (no SSL verify): {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"✅ Success! Response: {content}")
                        print()
                        print("⚠️  NOTE: SSL verification is disabled. This works but is not secure.")
                        print("   To fix SSL certificates, run: sudo apt-get update && sudo apt-get install ca-certificates")
                        return True
                    elif response.status_code == 401:
                        print(f"❌ 401 Unauthorized - API key might be invalid")
                        print(f"   Response: {response.text[:200]}")
                        return False
                    else:
                        print(f"❌ Error {response.status_code}: {response.text[:200]}")
                        return False
            except Exception as e2:
                print(f"❌ Connection failed: {e2}")
                return False
        else:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama_cloud())
    sys.exit(0 if success else 1)

