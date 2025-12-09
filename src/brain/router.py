"""Router: Decides between local and cloud inference based on complexity."""

import logging
from typing import Literal, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class InferenceTarget(str, Enum):
    """Target for inference routing."""
    LOCAL = "local"
    CLOUD = "cloud"


class Router:
    """
    Router decides whether to use local (Ollama) or cloud (Ollama Cloud) inference.
    
    Uses heuristics based on:
    - Query complexity
    - Context size
    - Task type
    - Tool requirements (NOTE: Currently routes tool queries to cloud because
      local Llama 3.2 3B doesn't support function calling yet)
    """
    
    # Keywords that suggest complex reasoning (route to cloud)
    COMPLEX_KEYWORDS = [
        "summarize", "compare", "analyze", "explain", "synthesize",
        "multi-step", "reasoning", "complex", "detailed analysis",
        "write", "generate", "create", "design",
        "medical", "diagnosis", "report", "research", "study",
        "evaluate", "assess", "interpret", "examine"
    ]
    
    # Keywords that suggest tool/API requirements
    # NOTE: Currently routes to cloud because local Llama 3.2 3B doesn't support
    # function calling. Once local brain supports function calling, we can route
    # simple tool queries (like "what's the weather?") to local first.
    TOOL_KEYWORDS = [
        # Weather tools
        "weather", "temperature", "forecast", "rain", "snow", "sunny",
        # Calendar/time tools
        "calendar", "schedule", "appointment", "meeting",
        "time", "date", "today", "tomorrow", "now",
        # Home automation
        "control", "turn on", "turn off", "set", "adjust",
        # Search tools (Wikipedia, ArXiv, Web, News)
        "search", "find", "lookup", "look up", "wikipedia", "arxiv", "arxiv.org",
        "web search", "search the web", "search web", "duckduckgo",
        "news", "headlines", "latest news", "tech news", "research papers",
        "papers", "scientific papers", "recent papers"
    ]
    
    # Keywords that suggest simple/local tasks
    SIMPLE_KEYWORDS = [
        "what", "when", "where", "who", "how much", "how many",
        "yes", "no", "true", "false", "quick", "simple"
    ]
    
    # Context size thresholds (in tokens, approximate)
    LARGE_CONTEXT_THRESHOLD = 4000
    MEDIUM_CONTEXT_THRESHOLD = 2000
    
    def __init__(
        self,
        prefer_local: bool = True,
        max_local_context: int = LARGE_CONTEXT_THRESHOLD,
        route_tools_to_cloud: bool = True
    ):
        """
        Initialize router.
        
        Args:
            prefer_local: Prefer local inference when possible (default True)
            max_local_context: Max context size for local inference (tokens)
            route_tools_to_cloud: Route tool-requiring queries to cloud (default True)
                                 Set to False once local brain supports function calling
        """
        self.prefer_local = prefer_local
        self.max_local_context = max_local_context
        self.route_tools_to_cloud = route_tools_to_cloud
        
    def route(
        self,
        query: str,
        context_size: int = 0,
        task_hint: Optional[str] = None,
        force_target: Optional[InferenceTarget] = None
    ) -> InferenceTarget:
        """
        Route query to local or cloud inference.
        
        Args:
            query: User query/prompt
            context_size: Size of context in tokens (approximate)
            task_hint: Optional hint about task type ("code", "reasoning", etc.)
            force_target: Force a specific target (overrides routing logic)
            
        Returns:
            InferenceTarget.LOCAL or InferenceTarget.CLOUD
        """
        # Force override takes precedence
        if force_target:
            logger.info(f"Router: Forced to {force_target.value}")
            return force_target
            
        # Check context size first
        if context_size > self.max_local_context:
            logger.info(f"Router: Large context ({context_size} tokens) -> CLOUD")
            return InferenceTarget.CLOUD
            
        # Task hint routing
        if task_hint:
            if task_hint in ["code", "simple", "quick"]:
                logger.info(f"Router: Task hint '{task_hint}' -> LOCAL")
                return InferenceTarget.LOCAL
            elif task_hint in ["reasoning", "complex", "analysis"]:
                logger.info(f"Router: Task hint '{task_hint}' -> CLOUD")
                return InferenceTarget.CLOUD
                
        # Heuristic-based routing
        query_lower = query.lower()
        
        # Check for complex keywords
        complex_score = sum(1 for keyword in self.COMPLEX_KEYWORDS if keyword in query_lower)
        simple_score = sum(1 for keyword in self.SIMPLE_KEYWORDS if keyword in query_lower)
        
        # Check for tool-requiring keywords
        tool_score = sum(1 for keyword in self.TOOL_KEYWORDS if keyword in query_lower)
        
        # Routing logic (prioritized):
        # 1. High complexity → cloud
        # 2. Tool keywords → cloud (if route_tools_to_cloud is True)
        #    NOTE: This is because local Llama 3.2 3B doesn't support function calling yet
        # 3. Simple queries → local
        
        if self.prefer_local:
            # High complexity → cloud
            if complex_score >= 2 or (complex_score >= 1 and context_size > self.MEDIUM_CONTEXT_THRESHOLD):
                logger.info(f"Router: Complex query (score={complex_score}) -> CLOUD")
                return InferenceTarget.CLOUD
            
            # Tool keywords → cloud (only if route_tools_to_cloud is enabled)
            # TODO: Once local brain supports function calling, we can route simple
            # tool queries (like "what's the weather?") to local first
            if tool_score > 0 and self.route_tools_to_cloud:
                logger.info(
                    f"Router: Tool-requiring query (keywords={tool_score}) -> CLOUD "
                    f"(local brain doesn't support function calling yet)"
                )
                return InferenceTarget.CLOUD
            
            # Simple query → local
            logger.info(f"Router: Simple query (score={simple_score}) -> LOCAL")
            return InferenceTarget.LOCAL
        else:
            # If not preferring local, use cloud for anything non-trivial
            if complex_score > 0 or context_size > self.MEDIUM_CONTEXT_THRESHOLD:
                return InferenceTarget.CLOUD
            elif tool_score > 0:
                return InferenceTarget.CLOUD
            else:
                return InferenceTarget.LOCAL
