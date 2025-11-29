"""Default tool registry with all tools pre-registered."""

from src.tools.tool_registry import ToolRegistry
from src.tools.weather_tool import WeatherTool
from src.tools.time_tool import TimeTool
from src.tools.knowledge_tool import WikipediaTool, ArxivTool
from src.tools.search_tool import DuckDuckGoTool, NewsTool


def create_default_registry() -> ToolRegistry:
    """
    Create a ToolRegistry with all default tools registered.
    
    Returns:
        ToolRegistry instance with all tools registered
    """
    registry = ToolRegistry()
    
    # Register all tools
    registry.register(WeatherTool())
    registry.register(TimeTool())
    registry.register(WikipediaTool())
    registry.register(ArxivTool())
    registry.register(DuckDuckGoTool())
    registry.register(NewsTool())
    
    return registry

