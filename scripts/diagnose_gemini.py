#!/usr/bin/env python3
"""Diagnostic script to test Gemini API key and connection."""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_gemini_api():
    """Test Gemini API with different model names."""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print("\nTesting different model names...\n")
    
    # Try different model names
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-pro",
    ]
    
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    payload = {
        "contents": [{
            "parts": [{"text": "Say hello"}]
        }],
        "generationConfig": {
            "maxOutputTokens": 10
        }
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for model in models_to_test:
            url = f"{base_url}/models/{model}:generateContent"
            params = {"key": api_key}
            
            try:
                response = await client.post(
                    url,
                    json=payload,
                    params=params,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {model}: SUCCESS")
                    if "candidates" in result:
                        text = result["candidates"][0]["content"]["parts"][0]["text"]
                        print(f"   Response: {text[:50]}...")
                    return model  # Return the first working model
                elif response.status_code == 401:
                    print(f"❌ {model}: UNAUTHORIZED (Invalid API key)")
                    print(f"   Response: {response.text[:200]}")
                    return None
                elif response.status_code == 404:
                    print(f"⚠️  {model}: NOT FOUND (Model doesn't exist or wrong endpoint)")
                elif response.status_code == 403:
                    print(f"❌ {model}: FORBIDDEN (API key doesn't have access)")
                    print(f"   Response: {response.text[:200]}")
                else:
                    print(f"❌ {model}: ERROR {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ {model}: EXCEPTION - {e}")
    
    print("\n❌ None of the model names worked.")
    print("\n💡 Troubleshooting:")
    print("   1. Verify your API key at: https://makersuite.google.com/app/apikey")
    print("   2. Make sure the key is for 'Gemini API' (not Vertex AI)")
    print("   3. Check if there are any usage limits or restrictions")
    return None

if __name__ == "__main__":
    asyncio.run(test_gemini_api())


