"""Orchestrator: Coordinates Local Brain and Cloud Burst based on router decisions."""

import logging
import json
from typing import Optional, Tuple, List, Dict, Any

from src.brain.local_brain import LocalBrain
from src.brain.cloud_brain import CloudBrain
from src.brain.router import Router, InferenceTarget
from src.brain.tool_executor import ToolExecutor
from src.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# Optional RAG import (Phase 4)
try:
    from src.memory.rag_server import RAGServer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    RAGServer = None


class Orchestrator:
    """
    Main orchestrator that coordinates local and cloud inference.
    
    Uses the Router to decide between Local Brain (Llama 3.2 3B) and
    Cloud Burst (Gemini 2.0 Flash) based on query complexity and requirements.
    """
    
    def __init__(
        self,
        prefer_local: bool = True,
        cloud_model: str = "gemini-2.0-flash",
        tool_registry: Optional[ToolRegistry] = None,
        rag_server: Optional["RAGServer"] = None,
        use_rag: bool = True
    ):
        """
        Initialize orchestrator.
        
        Args:
            prefer_local: Prefer local inference when possible
            cloud_model: Cloud model to use (Gemini variant)
            tool_registry: ToolRegistry instance (creates default if None)
            rag_server: RAGServer instance for long-term memory (optional)
            use_rag: Whether to use RAG context when available (default: True)
        """
        self.router = Router(prefer_local=prefer_local)
        self.cloud_model = cloud_model
        self.local_brain: Optional[LocalBrain] = None
        self.cloud_brain: Optional[CloudBrain] = None
        
        # Initialize tool registry and executor
        if tool_registry is None:
            from src.tools.default_registry import create_default_registry
            tool_registry = create_default_registry()
        self.tool_registry = tool_registry
        self.tool_executor = ToolExecutor(tool_registry)
        
        # Initialize RAG server (optional)
        self.rag_server = rag_server
        self.use_rag = use_rag and RAG_AVAILABLE and rag_server is not None
        if self.use_rag:
            logger.info("RAG Server enabled for long-term memory")
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.local_brain = LocalBrain()
        await self.local_brain.__aenter__()
        
        # Only initialize cloud brain if API key is available
        try:
            self.cloud_brain = CloudBrain(model=self.cloud_model)
            await self.cloud_brain.__aenter__()
        except ValueError as e:
            logger.warning(f"Cloud Brain not available: {e}")
            self.cloud_brain = None
            
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.local_brain:
            await self.local_brain.__aexit__(exc_type, exc_val, exc_tb)
        if self.cloud_brain:
            await self.cloud_brain.__aexit__(exc_type, exc_val, exc_tb)
            
    async def think(
        self,
        query: str,
        context_size: int = 0,
        task_hint: Optional[str] = None,
        force_target: Optional[InferenceTarget] = None,
        max_tool_iterations: int = 3,
        use_rag_context: Optional[bool] = None
    ) -> Tuple[str, InferenceTarget, List[Dict[str, Any]]]:
        """
        Process a query using the appropriate brain, with tool support and RAG context.
        
        Args:
            query: User query/prompt
            context_size: Size of context in tokens (for routing)
            task_hint: Optional hint about task type
            force_target: Force local or cloud (overrides router)
            max_tool_iterations: Maximum tool call iterations (to prevent loops)
            use_rag_context: Override RAG usage for this query (None = use default)
            
        Returns:
            Tuple of (response, target_used, tool_calls_made)
            
        Raises:
            RuntimeError: If neither brain is available
        """
        # Retrieve RAG context if enabled
        rag_context = None
        if (use_rag_context if use_rag_context is not None else self.use_rag):
            rag_context = await self._get_rag_context(query)
        
        # Enhance query with RAG context if available
        enhanced_query = query
        if rag_context:
            enhanced_query = f"{rag_context}\n\nUser Query: {query}"
            logger.info(f"RAG: Retrieved {len(rag_context.split('[Context')) - 1} context chunks")
        
        # Route the query
        target = self.router.route(enhanced_query, context_size, task_hint, force_target)
        
        tool_calls_made = []
        
        # Route to appropriate brain
        if target == InferenceTarget.CLOUD:
            if not self.cloud_brain:
                logger.warning("Cloud Brain not available, falling back to Local Brain")
                target = InferenceTarget.LOCAL
            else:
                logger.info("Orchestrator: Using Cloud Burst (Gemini 2.0 Flash)")
                response, tool_calls = await self._think_with_tools(
                    enhanced_query,
                    max_tool_iterations
                )
                return response, InferenceTarget.CLOUD, tool_calls
                
        # Use local brain (default or fallback)
        if not self.local_brain:
            raise RuntimeError("Local Brain is not available")
            
        logger.info("Orchestrator: Using Local Brain (Llama 3.2 3B)")
        # Note: Local brain doesn't support function calling yet
        # If query needs tools, router should have routed to cloud
        response = await self.local_brain.think(enhanced_query)
        return response, InferenceTarget.LOCAL, tool_calls_made
    
    async def _get_rag_context(self, query: str) -> Optional[str]:
        """
        Retrieve RAG context for a query.
        
        Args:
            query: User query
            
        Returns:
            Formatted context string or None if no context found
        """
        if not self.rag_server:
            return None
        
        try:
            chunks = await self.rag_server.retrieve_context(query, top_k=5, min_score=0.3)
            
            if not chunks:
                return None
            
            # Format context using retriever (works with both tiered and single collection)
            from src.memory.retriever import Retriever
            if self.rag_server.enable_tiering:
                retriever = self.rag_server.retriever  # Already initialized with tiering
            else:
                retriever = Retriever(self.rag_server.collection)
            return retriever.format_context(chunks)
            
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return None
        
    async def _think_with_tools(
        self,
        query: str,
        max_iterations: int = 3
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Think with tool support (for Cloud Brain).
        
        Handles function calling loop with proper conversation history:
        1. Send query with available tools
        2. If LLM requests tools, execute them
        3. Send tool results back to LLM with full conversation history
        4. Repeat until final answer or max iterations
        
        Args:
            query: User query
            max_iterations: Maximum tool call iterations
            
        Returns:
            Tuple of (final response, tool_calls_made)
        """
        # Get tool schemas for function calling
        tools = self.tool_registry.list_tools()
        tool_schemas = []
        
        for tool in tools:
            # Convert to Gemini function declaration format
            params = tool.get("parameters", {})
            tool_schemas.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameters": params
            })
        
        # Maintain conversation history for Gemini API
        # Format: [{"role": "user", "parts": [...]}, {"role": "model", "parts": [...]}, ...]
        conversation_history: List[Dict[str, Any]] = []
        tool_calls_made = []  # Track tool calls made during this query
        
        # First turn: User's query
        conversation_history.append({
            "role": "user",
            "parts": [{"text": query}]
        })
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Orchestrator: Tool iteration {iteration}/{max_iterations}")
            
            # Call Cloud Brain with full conversation history
            response = await self.cloud_brain.think_with_history(
                conversation_history,
                tools=tool_schemas if iteration == 1 else None  # Only send tools on first call
            )
            
            # Check if response contains function calls
            function_calls = self.tool_executor.parse_function_calls(response)
            
            if not function_calls:
                # No function calls, return the text response
                return response, tool_calls_made
            
            # Add model's function call to conversation history
            model_parts = []
            for func_call in function_calls:
                # Reconstruct function call in Gemini format
                model_parts.append({
                    "functionCall": {
                        "name": func_call.get("name"),
                        "args": func_call.get("args", {})
                    }
                })
            conversation_history.append({
                "role": "model",
                "parts": model_parts
            })
            
            # Execute function calls
            logger.info(f"Orchestrator: Executing {len(function_calls)} tool(s)")
            function_results = await self.tool_executor.execute_function_calls(function_calls)
            
            # Track tool calls
            for func_call in function_calls:
                tool_calls_made.append({
                    "tool": func_call.get("name"),
                    "args": func_call.get("args", {})
                })
            
            # Add function responses to conversation history (user's turn)
            # Function results are already in the correct format: [{"functionResponse": {...}}]
            conversation_history.append({
                "role": "user",
                "parts": function_results
            })
        
        # If we hit max iterations, return the last response
        logger.warning(f"Orchestrator: Reached max tool iterations ({max_iterations})")
        return response, tool_calls_made

