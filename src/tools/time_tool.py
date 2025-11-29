"""Time and date tool for getting current time information."""

import logging
from datetime import datetime
from typing import Dict, Any
from src.tools.base_tool import Tool

logger = logging.getLogger(__name__)


class TimeTool(Tool):
    """
    Tool for getting current time and date information.
    
    No API key required - uses system time.
    """
    
    def __init__(self):
        """Initialize Time tool."""
        super().__init__(
            name="get_time",
            description="Get current time and date information. Returns current time, date, and timezone."
        )
        
    def _get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for time tool."""
        return {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone (e.g., 'UTC', 'America/New_York'). Defaults to system timezone.",
                    "default": "local"
                },
                "format": {
                    "type": "string",
                    "enum": ["full", "time", "date"],
                    "description": "Output format: 'full' (time and date), 'time' (time only), 'date' (date only)",
                    "default": "full"
                }
            },
            "required": []
        }
        
    async def execute(
        self,
        timezone: str = "local",
        format: str = "full"
    ) -> Dict[str, Any]:
        """
        Get current time information.
        
        Args:
            timezone: Timezone (defaults to local)
            format: Output format (full/time/date)
            
        Returns:
            Dict with time information
        """
        now = datetime.now()
        
        if format == "time":
            result = {
                "time": now.strftime("%H:%M:%S"),
                "timezone": timezone
            }
        elif format == "date":
            result = {
                "date": now.strftime("%Y-%m-%d"),
                "day_of_week": now.strftime("%A")
            }
        else:  # full
            result = {
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "timezone": timezone
            }
            
        return {"result": result}

