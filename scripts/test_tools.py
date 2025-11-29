#!/usr/bin/env python3
"""Test script to verify all tools are properly registered and structured."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.default_registry import create_default_registry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_tool_registry():
    """Test that all tools are registered correctly."""
    print("\n" + "="*60)
    print("Mini-JARVIS: Tool Registry Test")
    print("="*60)
    
    # Create registry with all tools
    registry = create_default_registry()
    
    # List all tools
    print("\n📦 Registered Tools:")
    tools = registry.list_tools()
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool['name']}")
        print(f"     Description: {tool['description'][:60]}...")
    
    print(f"\n✅ Total tools registered: {len(tools)}")
    
    # Test tool schemas
    print("\n🔍 Tool Schemas:")
    for tool in tools:
        print(f"\n  Tool: {tool['name']}")
        params = tool.get('parameters', {})
        required = params.get('required', [])
        properties = params.get('properties', {})
        print(f"    Required params: {required if required else 'None'}")
        print(f"    Optional params: {len(properties) - len(required)}")
    
    # Test tool execution (Time tool - no API key needed)
    print("\n🧪 Testing Time Tool (no API key required):")
    try:
        result = await registry.execute_tool("get_time", format="full")
        print(f"  ✅ Time tool executed successfully")
        print(f"  Result: {result.get('result', {})}")
    except Exception as e:
        print(f"  ❌ Time tool failed: {e}")
    
    print("\n" + "="*60)
    print("✅ Tool registry test complete!")
    print("="*60)
    print("\n💡 Note: Other tools require API keys or libraries to be installed.")
    print("   Install dependencies: pip install -r requirements.txt\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_tool_registry())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")

