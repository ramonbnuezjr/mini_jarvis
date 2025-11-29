"""Cloud Brain: Gemini 2.0 Flash API client for complex reasoning and tool-use."""

import logging
import httpx
import os
import json
from typing import Optional, List, Dict, Any
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
            
    async def think_with_history(
        self,
        conversation_history: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate a response using Gemini API with full conversation history.
        
        This method maintains proper conversation context for function calling.
        The conversation_history should follow Gemini's format:
        [
            {"role": "user", "parts": [{"text": "..."}]},
            {"role": "model", "parts": [{"functionCall": {...}}]},
            {"role": "user", "parts": [{"functionResponse": {...}}]},
            ...
        ]
        
        Args:
            conversation_history: Full conversation history in Gemini format
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            tools: Optional list of tool schemas for function calling
            
        Returns:
            Generated text response or JSON string with function calls
            
        Raises:
            httpx.HTTPError: If Gemini API request fails
            ValueError: If API key is missing or response is invalid
        """
        if not self._client:
            raise RuntimeError("CloudBrain must be used as async context manager")
            
        url = f"{self.BASE_URL}/models/{self.model}:generateContent"
        
        payload = {
            "contents": conversation_history,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        # Add tools if provided (for function calling)
        if tools:
            payload["tools"] = [{
                "functionDeclarations": tools
            }]
        
        params = {
            "key": self.api_key
        }
        
        try:
            logger.info(f"CloudBrain: Thinking with {self.model} (history: {len(conversation_history)} turns)...")
            response = await self._client.post(
                url,
                json=payload,
                params=params,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                # Check for function calls
                function_calls = []
                text_response = None
                
                for part in parts:
                    if "functionCall" in part:
                        # Gemini function call format: {"name": "...", "args": {...}}
                        fc = part["functionCall"]
                        function_calls.append({
                            "name": fc.get("name", ""),
                            "args": fc.get("args", {})
                        })
                    elif "text" in part:
                        text_response = part["text"].strip()
                
                # If there are function calls, return them for execution
                if function_calls:
                    logger.info(f"CloudBrain: Model requested {len(function_calls)} function call(s)")
                    # Return function calls as JSON string for parsing
                    return json.dumps({
                        "function_calls": function_calls,
                        "text": text_response or ""
                    })
                
                # Return text response
                if text_response:
                    logger.info(f"CloudBrain: Generated {len(text_response)} chars")
                    return text_response
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
            elif response.status_code == 400:
                # Log the request payload for debugging
                logger.error(f"CloudBrain: Bad request. History length: {len(conversation_history)}")
                logger.debug(f"CloudBrain: Payload: {json.dumps(payload, indent=2)}")
                raise ValueError(f"Bad request to Gemini API: {e}. Check conversation history format.")
            raise
        except Exception as e:
            logger.error(f"CloudBrain: Unexpected error - {e}")
            raise
            
    async def think(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        function_responses: Optional[List[Dict[str, Any]]] = None
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
        
        # Build contents array
        contents = []
        
        # If we have function responses, this is a follow-up after tool execution
        # Gemini expects: user -> model (with function call) -> user (with function response) -> model (final answer)
        if function_responses:
            # Add function responses as user message (this is the response to the model's function call)
            contents.append({
                "role": "user",
                "parts": function_responses
            })
            # Don't add a new prompt - Gemini will generate final answer from function results
        else:
            # First turn: user's query
            parts = []
            if system_prompt:
                parts.append({"text": f"{system_prompt}\n\nUser: {prompt}\nAssistant:"})
            else:
                parts.append({"text": prompt})
            
            contents.append({
                "role": "user",
                "parts": parts
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        # Add tools if provided (for function calling)
        if tools:
            payload["tools"] = [{
                "functionDeclarations": tools
            }]
        
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
                candidate = result["candidates"][0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                # Check for function calls
                function_calls = []
                text_response = None
                
                for part in parts:
                    if "functionCall" in part:
                        # Gemini function call format: {"name": "...", "args": {...}}
                        fc = part["functionCall"]
                        function_calls.append({
                            "name": fc.get("name", ""),
                            "args": fc.get("args", {})
                        })
                    elif "text" in part:
                        text_response = part["text"].strip()
                
                # If there are function calls, return them for execution
                if function_calls:
                    logger.info(f"CloudBrain: Model requested {len(function_calls)} function call(s)")
                    # Return function calls as JSON string for parsing
                    return json.dumps({
                        "function_calls": function_calls,
                        "text": text_response or ""
                    })
                
                # Return text response
                if text_response:
                    logger.info(f"CloudBrain: Generated {len(text_response)} chars")
                    return text_response
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

