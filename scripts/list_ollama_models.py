#!/usr/bin/env python3
"""List available models from Ollama Cloud API."""

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

async def list_models():
    api_key = os.getenv("OLLAMA_CLOUD_API_KEY")
    base_url = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://api.ollama.cloud/v1")
    
    if not api_key:
        print("❌ OLLAMA_CLOUD_API_KEY not found")
        return
    
    url = f"{base_url}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                models = result.get('data', [])
                print(f"✅ Found {len(models)} available models:\n")
                for model in models:
                    model_id = model.get('id', 'unknown')
                    print(f"  - {model_id}")
                return models
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(list_models())

