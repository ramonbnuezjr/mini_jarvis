"""Orchestrator: Coordinates Local Brain and Cloud Burst based on router decisions."""

import logging
from typing import Optional

from src.brain.local_brain import LocalBrain
from src.brain.cloud_brain import CloudBrain
from src.brain.router import Router, InferenceTarget

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator that coordinates local and cloud inference.
    
    Uses the Router to decide between Local Brain (Llama 3.2 3B) and
    Cloud Burst (Gemini 2.0 Flash) based on query complexity and requirements.
    """
    
    def __init__(
        self,
        prefer_local: bool = True,
        cloud_model: str = "gemini-2.0-flash"
    ):
        """
        Initialize orchestrator.
        
        Args:
            prefer_local: Prefer local inference when possible
            cloud_model: Cloud model to use (Gemini variant)
        """
        self.router = Router(prefer_local=prefer_local)
        self.cloud_model = cloud_model
        self.local_brain: Optional[LocalBrain] = None
        self.cloud_brain: Optional[CloudBrain] = None
        
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
        force_target: Optional[InferenceTarget] = None
    ) -> tuple[str, InferenceTarget]:
        """
        Process a query using the appropriate brain.
        
        Args:
            query: User query/prompt
            context_size: Size of context in tokens (for routing)
            task_hint: Optional hint about task type
            force_target: Force local or cloud (overrides router)
            
        Returns:
            Tuple of (response, target_used)
            
        Raises:
            RuntimeError: If neither brain is available
        """
        # Route the query
        target = self.router.route(query, context_size, task_hint, force_target)
        
        # Route to appropriate brain
        if target == InferenceTarget.CLOUD:
            if not self.cloud_brain:
                logger.warning("Cloud Brain not available, falling back to Local Brain")
                target = InferenceTarget.LOCAL
            else:
                logger.info("Orchestrator: Using Cloud Burst (Gemini 2.0 Flash)")
                response = await self.cloud_brain.think(query)
                return response, InferenceTarget.CLOUD
                
        # Use local brain (default or fallback)
        if not self.local_brain:
            raise RuntimeError("Local Brain is not available")
            
        logger.info("Orchestrator: Using Local Brain (Llama 3.2 3B)")
        response = await self.local_brain.think(query)
        return response, InferenceTarget.LOCAL

