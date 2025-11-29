"""Base tool interface for Mini-JARVIS tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Base class for all tools in Mini-JARVIS."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize a tool.
        
        Args:
            name: Tool name (e.g., "get_weather")
            description: Tool description for LLM understanding
        """
        self.name = name
        self.description = description
        
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict with 'result' key containing tool output
        """
        pass
        
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM function calling.
        
        Returns:
            Dict describing tool parameters and return type
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters()
        }
    
    @abstractmethod
    def _get_parameters(self) -> Dict[str, Any]:
        """
        Get parameter schema for this tool.
        
        Returns:
            JSON Schema for tool parameters
        """
        pass

