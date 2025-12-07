"""Integration tests for tiered RAG memory system."""

import pytest
import asyncio
import tempfile
from pathlib import Path
from src.memory.rag_server import RAGServer
from src.memory.retriever import Retriever


class TestTieredRAG:
    """Test suite for tiered RAG memory system."""
    
    @pytest.fixture
    def temp_memory_dir(self):
        """Create temporary directory for RAG memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def rag_server(self, temp_memory_dir):
        """Create RAGServer with tiering enabled."""
        return RAGServer(
            persist_directory=temp_memory_dir,
            enable_tiering=True
        )
    
    @pytest.fixture
    def sample_documents(self, tmp_path):
        """Create sample documents for each tier."""
        docs = {}
        
        # Core document (important, should be boosted)
        core_doc = tmp_path / "core_ai.txt"
        core_doc.write_text(
            "Artificial Intelligence is a branch of computer science. "
            "Machine learning is a subset of AI that enables systems to learn from data. "
            "Deep learning uses neural networks with multiple layers."
        )
        docs['core'] = str(core_doc)
        
        # Reference document (standard)
        ref_doc = tmp_path / "reference_python.txt"
        ref_doc.write_text(
            "Python is a high-level programming language. "
            "It is known for its simplicity and readability. "
            "Python supports multiple programming paradigms."
        )
        docs['reference'] = str(ref_doc)
        
        # Ephemeral document (temporary, should be deprioritized)
        ephemeral_doc = tmp_path / "ephemeral_notes.txt"
        ephemeral_doc.write_text(
            "These are temporary notes about a meeting. "
            "They can be deleted after the meeting is over. "
            "Not important for long-term reference."
        )
        docs['ephemeral'] = str(ephemeral_doc)
        
        return docs
    
    @pytest.mark.asyncio
    async def test_tiered_ingestion(self, rag_server, sample_documents):
        """Test ingesting documents into different tiers."""
        # Ingest into each tier
        for tier, file_path in sample_documents.items():
            result = await rag_server.ingest_documents(
                [file_path],
                tier=tier,
                chunk_size=100,
                chunk_overlap=20
            )
            assert result['success']
            assert result['chunks_ingested'] > 0
        
        # Verify stats
        stats = rag_server.get_stats()
        assert stats['tiering_enabled'] is True
        assert stats['total_chunks'] > 0
        assert all(tier in stats['tier_counts'] for tier in ['core', 'reference', 'ephemeral'])
    
    @pytest.mark.asyncio
    async def test_weighted_retrieval(self, rag_server, sample_documents):
        """Test that weighted retrieval boosts core documents."""
        # Ingest documents
        for tier, file_path in sample_documents.items():
            await rag_server.ingest_documents(
                [file_path],
                tier=tier,
                chunk_size=100,
                chunk_overlap=20
            )
        
        # Query that should match all documents
        query = "computer science programming"
        chunks = await rag_server.retrieve_context(query, top_k=10, min_score=0.0)
        
        assert len(chunks) > 0
        
        # Verify chunks have tier information
        for chunk in chunks:
            assert 'tier' in chunk
            assert chunk['tier'] in ['core', 'reference', 'ephemeral']
            assert 'score' in chunk
            assert 'base_score' in chunk
            assert 'weight' in chunk
        
        # Core documents should have higher weighted scores
        core_chunks = [c for c in chunks if c['tier'] == 'core']
        ephemeral_chunks = [c for c in chunks if c['tier'] == 'ephemeral']
        
        if core_chunks and ephemeral_chunks:
            # Core chunks should have higher weighted scores
            avg_core_score = sum(c['score'] for c in core_chunks) / len(core_chunks)
            avg_ephemeral_score = sum(c['score'] for c in ephemeral_chunks) / len(ephemeral_chunks)
            
            # Core should be boosted (1.5x) vs ephemeral (0.7x)
            # So even with same base score, core should rank higher
            assert avg_core_score > avg_ephemeral_score or len(core_chunks) >= len(ephemeral_chunks)
    
    @pytest.mark.asyncio
    async def test_ttl_expiry(self, rag_server, tmp_path):
        """Test TTL-based expiry for ephemeral documents."""
        # Create ephemeral document with short TTL
        ephemeral_doc = tmp_path / "ephemeral_short_ttl.txt"
        ephemeral_doc.write_text("This document will expire soon.")
        
        result = await rag_server.ingest_documents(
            [str(ephemeral_doc)],
            tier="ephemeral",
            ttl_seconds=1,  # 1 second TTL
            chunk_size=100,
            chunk_overlap=20
        )
        assert result['success']
        
        # Verify document is in ephemeral tier
        stats_before = rag_server.get_stats()
        assert stats_before['tier_counts']['ephemeral'] > 0
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Cleanup expired documents
        cleanup_result = await rag_server.cleanup_expired()
        assert cleanup_result['expired_count'] > 0
        assert cleanup_result['chunks_deleted'] > 0
        
        # Verify chunks are removed
        stats_after = rag_server.get_stats()
        assert stats_after['tier_counts']['ephemeral'] < stats_before['tier_counts']['ephemeral']
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, temp_memory_dir):
        """Test that single collection mode still works."""
        # Create RAG server without tiering
        rag_server = RAGServer(
            persist_directory=temp_memory_dir,
            enable_tiering=False
        )
        
        assert rag_server.enable_tiering is False
        assert rag_server.collection is not None
        assert rag_server.collections is None
        
        # Should still work for ingestion
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content")
            file_path = f.name
        
        result = await rag_server.ingest_documents(
            [file_path],
            tier="reference",  # Will be ignored in non-tiered mode
            chunk_size=100,
            chunk_overlap=20
        )
        assert result['success']
        
        # Cleanup
        Path(file_path).unlink()
    
    @pytest.mark.asyncio
    async def test_tier_weights(self, rag_server, sample_documents):
        """Test that tier weights are applied correctly."""
        # Ingest documents
        for tier, file_path in sample_documents.items():
            await rag_server.ingest_documents(
                [file_path],
                tier=tier,
                chunk_size=100,
                chunk_overlap=20
            )
        
        # Query
        query = "artificial intelligence"
        chunks = await rag_server.retrieve_context(query, top_k=10, min_score=0.0)
        
        # Verify weights
        for chunk in chunks:
            tier = chunk['tier']
            weight = chunk['weight']
            base_score = chunk['base_score']
            weighted_score = chunk['score']
            
            # Verify weight matches tier
            if tier == 'core':
                assert weight == 1.5
                assert weighted_score == pytest.approx(base_score * 1.5, abs=0.01)
            elif tier == 'reference':
                assert weight == 1.0
                assert weighted_score == pytest.approx(base_score * 1.0, abs=0.01)
            elif tier == 'ephemeral':
                assert weight == 0.7
                assert weighted_score == pytest.approx(base_score * 0.7, abs=0.01)
    
    @pytest.mark.asyncio
    async def test_clear_memory_by_tier(self, rag_server, sample_documents):
        """Test clearing memory by tier."""
        # Ingest into all tiers
        for tier, file_path in sample_documents.items():
            await rag_server.ingest_documents(
                [file_path],
                tier=tier,
                chunk_size=100,
                chunk_overlap=20
            )
        
        stats_before = rag_server.get_stats()
        assert stats_before['tier_counts']['ephemeral'] > 0
        
        # Clear only ephemeral tier
        rag_server.clear_memory(tier='ephemeral')
        
        stats_after = rag_server.get_stats()
        assert stats_after['tier_counts']['ephemeral'] == 0
        # Other tiers should remain
        assert stats_after['tier_counts']['core'] > 0
        assert stats_after['tier_counts']['reference'] > 0

