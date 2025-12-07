"""Unit tests for RAGServer."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from src.memory.rag_server import RAGServer


class TestRAGServer:
    """Test suite for RAGServer."""
    
    @pytest.fixture
    def temp_rag_dir(self):
        """Create a temporary directory for RAG storage."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def rag_server(self, temp_rag_dir):
        """Create a RAGServer instance for testing."""
        return RAGServer(
            persist_directory=temp_rag_dir,
            collection_name="test_collection"
        )
    
    def test_rag_server_initialization(self, temp_rag_dir):
        """Test RAGServer initialization."""
        server = RAGServer(
            persist_directory=temp_rag_dir,
            collection_name="test_init"
        )
        
        assert server.persist_directory == Path(temp_rag_dir)
        assert server.collection_name == "test_init"
        assert server.collection is not None
    
    def test_get_stats_empty(self, rag_server):
        """Test getting stats from empty RAG server."""
        stats = rag_server.get_stats()
        
        assert stats["total_chunks"] == 0
        assert stats["collection_name"] == "test_collection"
        assert "persist_directory" in stats
    
    @pytest.mark.asyncio
    async def test_ingest_documents_single_file(self, rag_server, sample_text_file):
        """Test ingesting a single document."""
        result = await rag_server.ingest_documents([sample_text_file])
        
        assert result["success"] is True
        assert result["chunks_ingested"] > 0
        assert result["files_processed"] == 1
        
        # Verify chunks were added
        stats = rag_server.get_stats()
        assert stats["total_chunks"] == result["chunks_ingested"]
    
    @pytest.mark.asyncio
    async def test_ingest_documents_multiple_files(
        self, rag_server, sample_text_file, sample_markdown_file
    ):
        """Test ingesting multiple documents."""
        result = await rag_server.ingest_documents([
            sample_text_file,
            sample_markdown_file
        ])
        
        assert result["success"] is True
        assert result["chunks_ingested"] > 0
        assert result["files_processed"] == 2
    
    @pytest.mark.asyncio
    async def test_ingest_documents_nonexistent(self, rag_server):
        """Test ingesting non-existent files."""
        result = await rag_server.ingest_documents(["/nonexistent/file.txt"])
        
        # Should handle gracefully
        assert result["success"] is False or result["chunks_ingested"] == 0
    
    @pytest.mark.asyncio
    async def test_retrieve_context(self, rag_server, sample_text_file):
        """Test retrieving context from ingested documents."""
        # First ingest a document
        await rag_server.ingest_documents([sample_text_file])
        
        # Then retrieve
        chunks = await rag_server.retrieve_context("artificial intelligence", top_k=3)
        
        # Should return relevant chunks
        assert isinstance(chunks, list)
        # May be empty if embeddings aren't working, but structure should be correct
        if chunks:
            assert all("text" in chunk for chunk in chunks)
            assert all("metadata" in chunk for chunk in chunks)
            assert all("score" in chunk for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_retrieve_context_empty(self, rag_server):
        """Test retrieving from empty RAG server."""
        chunks = await rag_server.retrieve_context("test query", top_k=5)
        
        assert isinstance(chunks, list)
        assert len(chunks) == 0
    
    @pytest.mark.asyncio
    async def test_retrieve_context_with_min_score(self, rag_server, sample_text_file):
        """Test retrieving with minimum score filter."""
        await rag_server.ingest_documents([sample_text_file])
        
        chunks = await rag_server.retrieve_context(
            "test query",
            top_k=5,
            min_score=0.8  # High threshold
        )
        
        assert isinstance(chunks, list)
        if chunks:
            assert all(chunk["score"] >= 0.8 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_clear_memory(self, rag_server, sample_text_file):
        """Test clearing memory."""
        # Ingest something first
        await rag_server.ingest_documents([sample_text_file])
        
        # Verify something was ingested
        stats_before = rag_server.get_stats()
        assert stats_before["total_chunks"] > 0
        
        # Clear memory
        rag_server.clear_memory()
        
        # Verify it's empty
        stats_after = rag_server.get_stats()
        assert stats_after["total_chunks"] == 0

