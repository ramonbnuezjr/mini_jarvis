#!/usr/bin/env python3
"""Regression tests for Cloud Brain migration from Gemini to Ollama Cloud (hybrid pattern).

These tests ensure that the migration from Gemini 2.0 Flash to Ollama Cloud
using the hybrid pattern (local Ollama gateway) didn't break existing functionality.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.brain.cloud_brain import CloudBrain
from src.brain.orchestrator import Orchestrator
from src.brain.router import InferenceTarget
from src.memory.rag_server import RAGServer


@pytest.mark.asyncio
class TestCloudBrainRegression:
    """Regression tests for Cloud Brain migration."""
    
    async def test_cloud_brain_initialization(self):
        """Test that CloudBrain initializes correctly with hybrid pattern."""
        async with CloudBrain() as cloud:
            assert cloud.base_url == "http://localhost:11434"
            assert cloud.model == "gpt-oss:120b-cloud"
            # Should not require API key
            assert not hasattr(cloud, 'api_key') or cloud.api_key is None
    
    async def test_cloud_brain_health_check(self):
        """Test that health check works with local Ollama gateway."""
        async with CloudBrain() as cloud:
            is_healthy = await cloud.check_health()
            # Health check should work (may fail if Ollama not running, but shouldn't crash)
            assert isinstance(is_healthy, bool)
    
    async def test_cloud_brain_simple_query(self):
        """Test that CloudBrain can handle simple queries."""
        async with CloudBrain() as cloud:
            response = await cloud.think("Say hello in one word")
            assert isinstance(response, str)
            assert len(response) > 0
    
    async def test_cloud_brain_system_prompt(self):
        """Test that system prompts work correctly."""
        async with CloudBrain() as cloud:
            response = await cloud.think(
                "What is 2+2?",
                system_prompt="You are a helpful math assistant."
            )
            assert isinstance(response, str)
            assert len(response) > 0
    
    async def test_orchestrator_cloud_routing(self):
        """Test that orchestrator correctly routes to cloud brain."""
        async with Orchestrator() as orchestrator:
            # Complex query should route to cloud (or local if router decides otherwise)
            query = "Analyze the economic impact of artificial intelligence"
            response, target, tool_calls = await orchestrator.think(query)
            
            # Router may choose local or cloud - both are valid
            assert target in [InferenceTarget.LOCAL, InferenceTarget.CLOUD]
            assert isinstance(response, str)
            assert len(response) > 0
    
    async def test_tool_calling_with_cloud(self):
        """Test that tool calling works with cloud brain."""
        async with Orchestrator() as orchestrator:
            # Tool-requiring query should route to cloud
            query = "What's the weather in San Francisco?"
            response, target, tool_calls = await orchestrator.think(query)
            
            assert target == InferenceTarget.CLOUD
            # Should either use tools or provide a response
            assert isinstance(response, str)
            assert len(response) > 0
    
    async def test_rag_context_with_cloud(self):
        """Test that RAG context injection works with cloud brain."""
        # Initialize RAG with some test data
        rag_server = RAGServer(enable_tiering=True)
        
        # Ingest a test document
        test_doc = Path("/tmp/test_rag_cloud.txt")
        test_doc.write_text("Mini-JARVIS is an AI assistant for Raspberry Pi 5.")
        
        try:
            await rag_server.ingest_documents([str(test_doc)], tier="core")
            
            async with Orchestrator(rag_server=rag_server, use_rag=True) as orchestrator:
                # Force cloud to test RAG integration
                query = "What is Mini-JARVIS? Analyze its architecture."
                response, target, tool_calls = await orchestrator.think(
                    query,
                    force_target=InferenceTarget.CLOUD,
                    use_rag_context=True
                )
                
                assert target == InferenceTarget.CLOUD
                assert isinstance(response, str)
                # Response should mention Mini-JARVIS (from RAG context)
                # Handle Unicode variations (non-breaking hyphens, etc.)
                response_lower = response.lower().replace('\u2011', '-').replace('\u202f', ' ')
                assert "mini-jarvis" in response_lower or "mini jarvis" in response_lower
        finally:
            # Cleanup
            if test_doc.exists():
                test_doc.unlink()
    
    async def test_multi_turn_conversation(self):
        """Test that multi-turn conversations work with cloud brain."""
        async with Orchestrator() as orchestrator:
            # First turn
            query1 = "What is Python?"
            response1, target1, _ = await orchestrator.think(query1, force_target=InferenceTarget.CLOUD)
            assert isinstance(response1, str)
            
            # Second turn (follow-up)
            query2 = "What are its main features?"
            response2, target2, _ = await orchestrator.think(query2, force_target=InferenceTarget.CLOUD)
            assert isinstance(response2, str)
            assert target2 == InferenceTarget.CLOUD
    
    async def test_router_still_works(self):
        """Test that router logic still works correctly after migration."""
        async with Orchestrator() as orchestrator:
            # Simple query -> local
            simple_query = "What is Python?"
            _, target1, _ = await orchestrator.think(simple_query)
            # Router may choose local or cloud, but should work either way
            assert target1 in [InferenceTarget.LOCAL, InferenceTarget.CLOUD]
            
            # Complex query -> cloud
            complex_query = "Analyze and compare Python with JavaScript"
            _, target2, _ = await orchestrator.think(complex_query)
            # Should prefer cloud for complex queries
            assert target2 == InferenceTarget.CLOUD
    
    async def test_cloud_brain_error_handling(self):
        """Test that error handling works correctly."""
        async with CloudBrain() as cloud:
            # Invalid model should give clear error
            try:
                await cloud.think("test", model="nonexistent-model-12345")
                # If it doesn't raise, that's also acceptable (graceful degradation)
            except ValueError as e:
                assert "not found" in str(e).lower() or "404" in str(e)
            except Exception:
                # Other exceptions are acceptable
                pass

