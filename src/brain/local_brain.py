"""Local Brain: Ollama-based local LLM client for fast, private inference."""

import logging
import httpx
from typing import Optional, Dict, Any
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LocalBrain:
    """
    Local Brain using Ollama for on-device LLM inference.
    
    Designed for Raspberry Pi 5 with memory constraints in mind.
    Uses Llama 3.2 3B as default - fast, capable, and fits within 6GB RAM budget.
    If Llama 3.2 3B is insufficient, burst to cloud (Gemini 2.0 Flash) rather than larger local models.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: str = "llama3.2:3b",
        timeout: float = 600.0
    ):
        """
        Initialize Local Brain with Ollama connection.
        
        Args:
            base_url: Ollama API base URL (defaults to http://localhost:11434)
            default_model: Default model to use for inference
            timeout: Request timeout in seconds (default 10 min for Pi 5)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = default_model
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
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response using local Ollama model.
        
        Args:
            prompt: User prompt/question
            model: Model name (defaults to self.default_model)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
            
        Raises:
            httpx.HTTPError: If Ollama request fails
            ValueError: If model is invalid
        """
        if not self._client:
            raise RuntimeError("LocalBrain must be used as async context manager")
            
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        
        # Build full prompt with system message if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            logger.info(f"LocalBrain: Thinking with {model}...")
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "response" in result:
                response_text = result["response"].strip()
                logger.info(f"LocalBrain: Generated {len(response_text)} chars")
                return response_text
            else:
                raise ValueError(f"Unexpected Ollama response format: {result}")
                
        except httpx.HTTPError as e:
            logger.error(f"LocalBrain: HTTP error - {e}")
            raise
        except Exception as e:
            logger.error(f"LocalBrain: Unexpected error - {e}")
            raise
            
    async def check_health(self) -> bool:
        """
        Check if Ollama service is running and accessible.
        
        Returns:
            True if Ollama is healthy, False otherwise
        """
        if not self._client:
            raise RuntimeError("LocalBrain must be used as async context manager")
            
        try:
            url = f"{self.base_url}/api/tags"
            response = await self._client.get(url, timeout=5.0)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"LocalBrain: Health check failed - {e}")
            return False
            
    async def list_models(self) -> list[str]:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        if not self._client:
            raise RuntimeError("LocalBrain must be used as async context manager")
            
        try:
            url = f"{self.base_url}/api/tags"
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"LocalBrain: Failed to list models - {e}")
            return []

