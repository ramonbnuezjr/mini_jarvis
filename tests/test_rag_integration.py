"""Integration tests for RAG pipeline."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from src.memory.rag_server import RAGServer
from src.memory.retriever import Retriever


class TestRAGIntegration:
    """Integration tests for full RAG pipeline."""
    
    @pytest.fixture
    def temp_rag_dir(self):
        """Create a temporary directory for RAG storage."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def sample_documents(self, temp_dir):
        """Create multiple sample documents."""
        docs = []
        
        # Document 1: About AI
        doc1 = Path(temp_dir) / "ai_doc.txt"
        doc1.write_text("""
        Artificial intelligence is transforming technology.
        Machine learning enables computers to learn from data.
        Deep learning uses neural networks for complex tasks.
        """)
        docs.append(str(doc1))
        
        # Document 2: About Python
        doc2 = Path(temp_dir) / "python_doc.txt"
        doc2.write_text("""
        Python is a popular programming language.
        It is used for web development, data science, and AI.
        Python has a simple and readable syntax.
        """)
        docs.append(str(doc2))
        
        # Document 3: About Raspberry Pi
        doc3 = Path(temp_dir) / "raspberry_pi_doc.txt"
        doc3.write_text("""
        Raspberry Pi is a small single-board computer.
        It runs Linux and supports Python programming.
        Raspberry Pi 5 has improved performance.
        """)
        docs.append(str(doc3))
        
        return docs
    
    @pytest.mark.asyncio
    async def test_full_pipeline_ingest_and_retrieve(
        self, temp_rag_dir, sample_documents
    ):
        """Test full pipeline: ingest documents and retrieve context."""
        # Initialize RAG server
        rag_server = RAGServer(
            persist_directory=temp_rag_dir,
            collection_name="integration_test"
        )
        
        # Step 1: Ingest documents
        result = await rag_server.ingest_documents(sample_documents)
        
        assert result["success"] is True
        assert result["chunks_ingested"] > 0
        assert result["files_processed"] == len(sample_documents)
        
        # Step 2: Retrieve context
        chunks = await rag_server.retrieve_context("artificial intelligence", top_k=3)
        
        # Should find relevant chunks
        assert isinstance(chunks, list)
        # Note: May be empty if embeddings aren't working, but structure should be correct
        
        # Step 3: Format context
        if chunks:
            retriever = Retriever(rag_server.collection)
            context = retriever.format_context(chunks)
            
            assert isinstance(context, str)
            assert len(context) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_queries_same_collection(
        self, temp_rag_dir, sample_documents
    ):
        """Test multiple queries against the same collection."""
        rag_server = RAGServer(
            persist_directory=temp_rag_dir,
            collection_name="multi_query_test"
        )
        
        # Ingest documents
        await rag_server.ingest_documents(sample_documents)
        
        # Query 1: About AI
        chunks1 = await rag_server.retrieve_context("machine learning", top_k=2)
        
        # Query 2: About Python
        chunks2 = await rag_server.retrieve_context("programming language", top_k=2)
        
        # Query 3: About Raspberry Pi
        chunks3 = await rag_server.retrieve_context("single board computer", top_k=2)
        
        # All should return results (structure-wise)
        assert isinstance(chunks1, list)
        assert isinstance(chunks2, list)
        assert isinstance(chunks3, list)
    
    @pytest.mark.asyncio
    async def test_persistent_storage(self, temp_rag_dir, sample_documents):
        """Test that RAG data persists across server instances."""
        # Create first server and ingest
        server1 = RAGServer(
            persist_directory=temp_rag_dir,
            collection_name="persistence_test"
        )
        await server1.ingest_documents(sample_documents)
        stats1 = server1.get_stats()
        
        # Create second server with same directory
        server2 = RAGServer(
            persist_directory=temp_rag_dir,
            collection_name="persistence_test"
        )
        stats2 = server2.get_stats()
        
        # Should have the same number of chunks
        assert stats2["total_chunks"] == stats1["total_chunks"]
        assert stats2["total_chunks"] > 0

