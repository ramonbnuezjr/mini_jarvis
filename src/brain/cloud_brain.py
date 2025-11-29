"""Cloud Brain: Gemini 2.0 Flash API client for complex reasoning and tool-use."""

import logging
import httpx
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CloudBrain:
    """
    Cloud Brain using Google Gemini 2.0 API for complex reasoning.
    
    Used when local Llama 3.2 3B is insufficient or when tools are needed.
    Provides better reasoning, tool-use capabilities, and handles large contexts.
    """
    
    DEFAULT_MODEL = "gemini-2.0-flash"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0
    ):
        """
        Initialize Cloud Brain with Gemini API.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model name (defaults to gemini-2.0-flash)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in .env file or pass as argument."
            )
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        timeout_config = httpx.Timeout(
            connect=10.0,
            read=self.timeout,
            write=10.0,
            pool=10.0
        )
        self._client = httpx.AsyncClient(timeout=timeout_config)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            
    async def think(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response using Gemini API.
        
        Args:
            prompt: User prompt/question
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
            
        Raises:
            httpx.HTTPError: If Gemini API request fails
            ValueError: If API key is missing or response is invalid
        """
        if not self._client:
            raise RuntimeError("CloudBrain must be used as async context manager")
            
        url = f"{self.BASE_URL}/models/{self.model}:generateContent"
        
        # Build full prompt with system message if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        params = {
            "key": self.api_key
        }
        
        try:
            logger.info(f"CloudBrain: Thinking with {self.model}...")
            response = await self._client.post(
                url,
                json=payload,
                params=params,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0].get("content", {})
                parts = content.get("parts", [])
                if parts and "text" in parts[0]:
                    response_text = parts[0]["text"].strip()
                    logger.info(f"CloudBrain: Generated {len(response_text)} chars")
                    return response_text
                else:
                    raise ValueError("Unexpected response format from Gemini API")
            else:
                raise ValueError("No candidates in Gemini API response")
                
        except httpx.HTTPError as e:
            logger.error(f"CloudBrain: HTTP error - {e}")
            if response.status_code == 401:
                raise ValueError("Invalid Gemini API key. Check your GEMINI_API_KEY in .env")
            elif response.status_code == 429:
                raise ValueError("Gemini API rate limit exceeded. Please try again later.")
            raise
        except Exception as e:
            logger.error(f"CloudBrain: Unexpected error - {e}")
            raise
            
    async def check_health(self) -> bool:
        """
        Check if Gemini API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        if not self._client:
            raise RuntimeError("CloudBrain must be used as async context manager")
            
        try:
            # Try a minimal request to check API key validity
            url = f"{self.BASE_URL}/models/{self.model}:generateContent"
            payload = {
                "contents": [{"parts": [{"text": "test"}]}],
                "generationConfig": {"maxOutputTokens": 1}
            }
            params = {"key": self.api_key}
            
            response = await self._client.post(
                url,
                json=payload,
                params=params,
                headers={"Content-Type": "application/json"},
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"CloudBrain: Health check failed - {e}")
            return False

