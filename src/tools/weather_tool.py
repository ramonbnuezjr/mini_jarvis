"""Weather tool for getting current weather information."""

import logging
import httpx
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from src.tools.base_tool import Tool

load_dotenv()

logger = logging.getLogger(__name__)


class WeatherTool(Tool):
    """
    Tool for getting current weather information.
    
    Uses OpenWeatherMap API (free tier available).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Weather tool.
        
        Args:
            api_key: OpenWeatherMap API key (defaults to OPENWEATHER_API_KEY env var)
        """
        super().__init__(
            name="get_weather",
            description="Get current weather information for a location. Returns temperature, conditions, humidity, and wind speed."
        )
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        
    def _get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for weather tool."""
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or 'city,country' (e.g., 'London,UK' or 'New York')"
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial", "kelvin"],
                    "description": "Temperature units (default: metric)",
                    "default": "metric"
                }
            },
            "required": ["location"]
        }
        
    async def execute(
        self,
        location: str,
        units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Get weather for a location.
        
        Args:
            location: City name or 'city,country'
            units: Temperature units (metric/imperial/kelvin)
            
        Returns:
            Dict with weather information
        """
        if not self.api_key:
            return {
                "result": "Weather API key not configured. Set OPENWEATHER_API_KEY in .env file.",
                "error": "API_KEY_MISSING"
            }
            
        params = {
            "q": location,
            "appid": self.api_key,
            "units": units
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Format response
                result = {
                    "location": f"{data['name']}, {data['sys']['country']}",
                    "temperature": f"{data['main']['temp']:.1f}°{'C' if units == 'metric' else 'F' if units == 'imperial' else 'K'}",
                    "conditions": data['weather'][0]['description'].title(),
                    "humidity": f"{data['main']['humidity']}%",
                    "wind_speed": f"{data['wind']['speed']} m/s" if units == 'metric' else f"{data['wind']['speed']} mph",
                    "feels_like": f"{data['main']['feels_like']:.1f}°{'C' if units == 'metric' else 'F' if units == 'imperial' else 'K'}"
                }
                
                return {"result": result}
                
        except httpx.HTTPError as e:
            logger.error(f"Weather API error: {e}")
            return {
                "result": f"Failed to get weather: {str(e)}",
                "error": "API_ERROR"
            }
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return {
                "result": f"Error getting weather: {str(e)}",
                "error": "UNKNOWN_ERROR"
            }

