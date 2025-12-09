#!/usr/bin/env python3
"""Test Ollama Cloud with standard Ollama API format."""

import asyncio
import httpx
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def test_standard_format():
    api_key = os.getenv("OLLAMA_CLOUD_API_KEY")
    
    # Try different base URLs and endpoints
    configs = [
        ("https://api.ollama.cloud", "/api/chat"),
        ("https://api.ollama.cloud", "/api/generate"),
        ("https://api.ollama.cloud/v1", "/chat/completions"),
    ]
    
    for base_url, endpoint in configs:
        print(f"\n{'='*60}")
        print(f"Testing: {base_url}{endpoint}")
        print('='*60)
        
        url = f"{base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Try both formats
        payloads = [
            # Standard Ollama format
            {
                "model": "gpt-oss:120b-cloud",
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False
            },
            # OpenAI format
            {
                "model": "gpt-oss:120b-cloud",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            }
        ]
        
        for i, payload in enumerate(payloads):
            print(f"\n  Payload format {i+1}: {list(payload.keys())}")
            try:
                async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                    r = await client.post(url, json=payload, headers=headers)
                    print(f"  Status: {r.status_code}")
                    if r.status_code == 200:
                        result = r.json()
                        print(f"  ✅ SUCCESS!")
                        if "message" in result:
                            print(f"  Response: {result['message'].get('content', '')}")
                        elif "choices" in result:
                            print(f"  Response: {result['choices'][0]['message']['content']}")
                        else:
                            print(f"  Response: {result}")
                        return True
                    elif r.status_code == 401:
                        print(f"  ❌ 401 Unauthorized")
                    elif r.status_code == 404:
                        print(f"  ❌ 404 Not Found")
                    else:
                        print(f"  Response: {r.text[:200]}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_standard_format())
    sys.exit(0 if success else 1)

