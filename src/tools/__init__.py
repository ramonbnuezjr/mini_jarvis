"""Tools: MCP Server and tool implementations for Mini-JARVIS."""

from src.tools.base_tool import Tool
from src.tools.tool_registry import ToolRegistry
from src.tools.weather_tool import WeatherTool
from src.tools.time_tool import TimeTool
from src.tools.knowledge_tool import WikipediaTool, ArxivTool
from src.tools.search_tool import DuckDuckGoTool, NewsTool
from src.tools.default_registry import create_default_registry

__all__ = [
    "Tool",
    "ToolRegistry",
    "WeatherTool",
    "TimeTool",
    "WikipediaTool",
    "ArxivTool",
    "DuckDuckGoTool",
    "NewsTool",
    "create_default_registry"
]

