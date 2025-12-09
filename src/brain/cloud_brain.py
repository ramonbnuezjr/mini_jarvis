"""Cloud Brain: Ollama Cloud API client for complex reasoning and tool-use."""

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
    Cloud Brain using local Ollama gateway with cloud models for complex reasoning.
    
    Uses the hybrid pattern: local Ollama as the gateway, cloud models (gpt-oss:120b-cloud)
    are pulled and accessed via the local endpoint. Ollama automatically offloads to cloud.
    
    This provides:
    - Single API endpoint (local Ollama)
    - Same API format everywhere (OpenAI-compatible)
    - Automatic cloud offloading when using cloud model names
    - No need to manage cloud API keys in code (handled by `ollama signin`)
    """
    
    DEFAULT_MODEL = "gpt-oss:120b-cloud"
    DEFAULT_BASE_URL = "http://localhost:11434"
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0
    ):
        """
        Initialize Cloud Brain with local Ollama gateway.
        
        Args:
            base_url: Ollama API base URL (defaults to OLLAMA_BASE_URL env var or http://localhost:11434)
            model: Cloud model name (defaults to OLLAMA_CLOUD_MODEL env var or gpt-oss:120b-cloud)
            timeout: Request timeout in seconds
        """
        # Use same base URL as LocalBrain - local Ollama gateway
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", self.DEFAULT_BASE_URL)
        self.model = model or os.getenv("OLLAMA_CLOUD_MODEL", self.DEFAULT_MODEL)
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
        # Create client with SSL verification enabled
        self._client = httpx.AsyncClient(
            timeout=timeout_config,
            verify=True  # Enable SSL verification
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    def _convert_gemini_history_to_openai(
        self,
        gemini_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert Gemini conversation history format to OpenAI format.
        
        Gemini format:
        [
            {"role": "user", "parts": [{"text": "..."}]},
            {"role": "model", "parts": [{"functionCall": {...}}]},
            {"role": "user", "parts": [{"functionResponse": {...}}]},
        ]
        
        OpenAI format:
        [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": null, "tool_calls": [...]},
            {"role": "tool", "content": "...", "tool_call_id": "..."},
        ]
        """
        openai_messages = []
        
        for gemini_msg in gemini_history:
            role = gemini_msg.get("role", "")
            parts = gemini_msg.get("parts", [])
            
            if role == "user":
                # Check if this is a function response or regular user message
                has_function_response = any("functionResponse" in part for part in parts)
                
                if has_function_response:
                    # Convert function responses to OpenAI tool format
                    for part in parts:
                        if "functionResponse" in part:
                            func_resp = part["functionResponse"]
                            func_name = func_resp.get("name", "")
                            func_result = func_resp.get("response", {})
                            
                            # Format function result as JSON string
                            if isinstance(func_result, dict):
                                content = json.dumps(func_result, ensure_ascii=False)
                            else:
                                content = str(func_result)
                            
                            openai_messages.append({
                                "role": "tool",
                                "content": content,
                                "tool_call_id": func_name  # Use function name as ID
                            })
                else:
                    # Regular user message
                    text_parts = [part.get("text", "") for part in parts if "text" in part]
                    content = "\n".join(text_parts)
                    if content:
                        openai_messages.append({
                            "role": "user",
                            "content": content
                        })
            
            elif role == "model":
                # Check for function calls
                function_calls = []
                text_content = None
                
                for part in parts:
                    if "functionCall" in part:
                        func_call = part["functionCall"]
                        function_calls.append({
                            "id": func_call.get("name", ""),  # Use function name as ID
                            "type": "function",
                            "function": {
                                "name": func_call.get("name", ""),
                                "arguments": json.dumps(func_call.get("args", {}), ensure_ascii=False)
                            }
                        })
                    elif "text" in part:
                        text_content = part.get("text", "")
                
                if function_calls:
                    # Model made function calls
                    openai_messages.append({
                        "role": "assistant",
                        "content": text_content,
                        "tool_calls": function_calls
                    })
                elif text_content:
                    # Regular model response
                    openai_messages.append({
                        "role": "assistant",
                        "content": text_content
                    })
        
        return openai_messages
    
    def _convert_openai_to_gemini_format(
        self,
        openai_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert OpenAI format back to Gemini format for compatibility.
        
        This is used when we need to maintain Gemini format in orchestrator.
        """
        gemini_history = []
        
        for msg in openai_messages:
            role = msg.get("role", "")
            
            if role == "user":
                gemini_history.append({
                    "role": "user",
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            elif role == "assistant":
                parts = []
                
                # Check for tool calls
                if "tool_calls" in msg:
                    for tool_call in msg.get("tool_calls", []):
                        func = tool_call.get("function", {})
                        func_name = func.get("name", "")
                        func_args_str = func.get("arguments", "{}")
                        
                        try:
                            func_args = json.loads(func_args_str)
                        except json.JSONDecodeError:
                            func_args = {}
                        
                        parts.append({
                            "functionCall": {
                                "name": func_name,
                                "args": func_args
                            }
                        })
                
                # Add text content if present
                content = msg.get("content")
                if content:
                    parts.append({"text": content})
                
                if parts:
                    gemini_history.append({
                        "role": "model",
                        "parts": parts
                    })
            
            elif role == "tool":
                # Tool response
                tool_call_id = msg.get("tool_call_id", "")
                content = msg.get("content", "")
                
                try:
                    # Try to parse as JSON, fallback to string
                    response = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    response = content
                
                gemini_history.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": tool_call_id,
                            "response": response
                        }
                    }]
                })
        
        return gemini_history
            
    async def think_with_history(
        self,
        conversation_history: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate a response using Ollama Cloud API with full conversation history.
        
        This method maintains proper conversation context for function calling.
        Accepts conversation_history in Gemini format (for backward compatibility)
        and converts it to OpenAI format internally.
        
        Args:
            conversation_history: Full conversation history in Gemini format
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            tools: Optional list of tool schemas for function calling (OpenAI format)
            
        Returns:
            Generated text response or JSON string with function calls
            
        Raises:
            httpx.HTTPError: If Ollama Cloud API request fails
            ValueError: If API key is missing or response is invalid
        """
        if not self._client:
            raise RuntimeError("CloudBrain must be used as async context manager")
        
        # Convert Gemini format to OpenAI format
        openai_messages = self._convert_gemini_history_to_openai(conversation_history)
        
        # Use OpenAI-compatible endpoint with /v1 prefix
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add tools if provided (OpenAI format)
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"  # Let model decide when to use tools
        
        # Local Ollama doesn't require Bearer token (authentication handled by `ollama signin`)
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"CloudBrain: Thinking with {self.model} (history: {len(openai_messages)} messages)...")
            response = await self._client.post(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                message = choice.get("message", {})
                
                # Check for function calls (OpenAI format)
                function_calls = []
                text_response = None
                
                if "tool_calls" in message:
                    # Model requested function calls
                    for tool_call in message.get("tool_calls", []):
                        func = tool_call.get("function", {})
                        func_name = func.get("name", "")
                        func_args_str = func.get("arguments", "{}")
                        
                        try:
                            func_args = json.loads(func_args_str)
                        except json.JSONDecodeError:
                            func_args = {}
                        
                        function_calls.append({
                            "name": func_name,
                            "args": func_args
                        })
                
                # Get text content
                text_response = message.get("content")
                if text_response:
                    text_response = text_response.strip()
                
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
                    raise ValueError("Unexpected response format from Ollama API")
            else:
                raise ValueError("No choices in Ollama API response")
                
        except httpx.HTTPError as e:
            logger.error(f"CloudBrain: HTTP error - {e}")
            if hasattr(e, 'response') and e.response:
                status_code = e.response.status_code
                if status_code == 401:
                    raise ValueError("Unauthorized. Make sure you've run 'ollama signin' to authenticate with Ollama Cloud.")
                elif status_code == 429:
                    raise ValueError("Rate limit exceeded. Please try again later.")
                elif status_code == 400:
                    logger.error(f"CloudBrain: Bad request. History length: {len(openai_messages)}")
                    logger.debug(f"CloudBrain: Payload: {json.dumps(payload, indent=2)}")
                    raise ValueError(f"Bad request to Ollama API: {e}. Check conversation history format.")
                elif status_code == 404:
                    raise ValueError(f"Model '{self.model}' not found. Run 'ollama pull {self.model}' to download it.")
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
        Generate a response using Ollama Cloud API.
        
        Args:
            prompt: User prompt/question
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt for context
            tools: Optional list of tool schemas for function calling
            function_responses: Optional function responses (for follow-up after tool execution)
            
        Returns:
            Generated text response
            
        Raises:
            httpx.HTTPError: If Ollama Cloud API request fails
            ValueError: If API key is missing or response is invalid
        """
        if not self._client:
            raise RuntimeError("CloudBrain must be used as async context manager")
        
        # Use OpenAI-compatible endpoint with /v1 prefix
        url = f"{self.base_url}/v1/chat/completions"
        
        # Build messages array
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # If we have function responses, this is a follow-up after tool execution
        if function_responses:
            # Convert Gemini function response format to OpenAI tool format
            for func_resp in function_responses:
                if "functionResponse" in func_resp:
                    fr = func_resp["functionResponse"]
                    func_name = fr.get("name", "")
                    func_result = fr.get("response", {})
                    
                    if isinstance(func_result, dict):
                        content = json.dumps(func_result, ensure_ascii=False)
                    else:
                        content = str(func_result)
                    
                    messages.append({
                        "role": "tool",
                        "content": content,
                        "tool_call_id": func_name
                    })
        else:
            # First turn: user's query
            messages.append({
                "role": "user",
                "content": prompt
            })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add tools if provided (OpenAI format)
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        # Local Ollama doesn't require Bearer token (authentication handled by `ollama signin`)
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"CloudBrain: Thinking with {self.model}...")
            response = await self._client.post(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                message = choice.get("message", {})
                
                # Check for function calls
                function_calls = []
                text_response = None
                
                if "tool_calls" in message:
                    for tool_call in message.get("tool_calls", []):
                        func = tool_call.get("function", {})
                        func_name = func.get("name", "")
                        func_args_str = func.get("arguments", "{}")
                        
                        try:
                            func_args = json.loads(func_args_str)
                        except json.JSONDecodeError:
                            func_args = {}
                        
                        function_calls.append({
                            "name": func_name,
                            "args": func_args
                        })
                
                text_response = message.get("content")
                if text_response:
                    text_response = text_response.strip()
                
                # If there are function calls, return them for execution
                if function_calls:
                    logger.info(f"CloudBrain: Model requested {len(function_calls)} function call(s)")
                    return json.dumps({
                        "function_calls": function_calls,
                        "text": text_response or ""
                    })
                
                # Return text response
                if text_response:
                    logger.info(f"CloudBrain: Generated {len(text_response)} chars")
                    return text_response
                else:
                    raise ValueError("Unexpected response format from Ollama API")
            else:
                raise ValueError("No choices in Ollama API response")
                
        except httpx.HTTPError as e:
            logger.error(f"CloudBrain: HTTP error - {e}")
            if hasattr(e, 'response') and e.response:
                status_code = e.response.status_code
                if status_code == 401:
                    raise ValueError("Unauthorized. Make sure you've run 'ollama signin' to authenticate with Ollama Cloud.")
                elif status_code == 429:
                    raise ValueError("Rate limit exceeded. Please try again later.")
                elif status_code == 404:
                    raise ValueError(f"Model '{self.model}' not found. Run 'ollama pull {self.model}' to download it.")
            raise
        except Exception as e:
            logger.error(f"CloudBrain: Unexpected error - {e}")
            raise
            
    async def check_health(self) -> bool:
        """
        Check if local Ollama gateway is accessible and cloud model is available.
        
        Returns:
            True if Ollama is healthy and model is accessible, False otherwise
        """
        if not self._client:
            raise RuntimeError("CloudBrain must be used as async context manager")
        
        try:
            # Try a minimal request to check if local Ollama is accessible
            # Use OpenAI-compatible endpoint with /v1 prefix
            url = f"{self.base_url}/v1/chat/completions"
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            headers = {
                "Content-Type": "application/json"
            }
            
            response = await self._client.post(
                url,
                json=payload,
                headers=headers,
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"CloudBrain: Health check failed - {e}")
            return False
