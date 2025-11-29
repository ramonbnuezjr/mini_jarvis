"""Tool Executor: Handles function calling and tool execution for LLMs."""

import logging
import json
from typing import Dict, Any, List, Optional
from src.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes tools based on LLM function calls.
    
    Handles the interaction between LLMs and tools:
    1. Receives function calls from LLM
    2. Executes tools with provided parameters
    3. Formats results for LLM consumption
    """
    
    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize tool executor.
        
        Args:
            tool_registry: ToolRegistry instance with registered tools
        """
        self.registry = tool_registry
        
    async def execute_function_calls(
        self,
        function_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple function calls and return results.
        
        Args:
            function_calls: List of function call dicts from LLM
            
        Returns:
            List of function call results formatted for LLM
        """
        results = []
        
        for func_call in function_calls:
            function_name = func_call.get("name", "")
            args = func_call.get("args", {})
            
            try:
                # Execute the tool
                tool_result = await self.registry.execute_tool(function_name, **args)
                
                # Format result for LLM
                results.append({
                    "functionResponse": {
                        "name": function_name,
                        "response": tool_result
                    }
                })
                
                logger.info(f"ToolExecutor: Executed {function_name} successfully")
                
            except Exception as e:
                logger.error(f"ToolExecutor: Failed to execute {function_name}: {e}")
                # Return error result
                results.append({
                    "functionResponse": {
                        "name": function_name,
                        "response": {
                            "result": f"Error executing tool: {str(e)}",
                            "error": str(e)
                        }
                    }
                })
        
        return results
        
    def parse_function_calls(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse function calls from LLM response.
        
        Args:
            response: LLM response (may contain JSON with function calls)
            
        Returns:
            List of function calls or None if no function calls
        """
        try:
            # Try to parse as JSON (Gemini returns function calls as JSON string)
            data = json.loads(response)
            if "function_calls" in data:
                function_calls = data["function_calls"]
                # Convert Gemini format to our format
                # Gemini format: {"name": "...", "args": {...}}
                parsed_calls = []
                for fc in function_calls:
                    # Handle both direct format and nested format
                    if isinstance(fc, dict):
                        name = fc.get("name", "")
                        args = fc.get("args", {})
                        if name:  # Only add if we have a name
                            parsed_calls.append({
                                "name": name,
                                "args": args
                            })
                return parsed_calls if parsed_calls else None
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
            # Not a function call response, return None
            logger.debug(f"Not a function call response: {e}")
            pass
        
        return None

