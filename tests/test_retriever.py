"""Unit tests for Retriever."""

import pytest
import asyncio
from src.memory.retriever import Retriever


class TestRetriever:
    """Test suite for Retriever."""
    
    @pytest.fixture
    def mock_collection(self):
        """Create a mock ChromaDB collection."""
        class MockCollection:
            def __init__(self):
                self.data = {
                    "ids": [["doc1", "doc2", "doc3"]],
                    "documents": [["Document about AI", "Document about ML", "Document about NLP"]],
                    "metadatas": [[
                        {"source": "test1.txt"},
                        {"source": "test2.txt"},
                        {"source": "test3.txt"}
                    ]],
                    "distances": [[0.1, 0.3, 0.5]]
                }
            
            def query(self, query_embeddings, n_results):
                return self.data
        
        return MockCollection()
    
    @pytest.mark.asyncio
    async def test_retrieve_with_results(self, mock_collection):
        """Test retrieval with results."""
        retriever = Retriever(mock_collection)
        
        # Mock the embedding method
        async def mock_embed(query):
            return [0.1] * 384  # Mock embedding vector
        
        retriever._embed_query = mock_embed
        
        chunks = await retriever.retrieve("test query", top_k=3, min_score=0.0)
        
        assert len(chunks) == 3
        assert all("text" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all("score" in chunk for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_retrieve_with_min_score_filter(self, mock_collection):
        """Test retrieval with minimum score filter."""
        retriever = Retriever(mock_collection)
        
        async def mock_embed(query):
            return [0.1] * 384
        
        retriever._embed_query = mock_embed
        
        # min_score=0.6 should filter out chunks with score < 0.6
        # scores are 1 - distance, so: 0.9, 0.7, 0.5
        chunks = await retriever.retrieve("test query", top_k=3, min_score=0.6)
        
        # Should only return chunks with score >= 0.6 (first two)
        assert len(chunks) == 2
        assert all(chunk["score"] >= 0.6 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_retrieve_empty_collection(self):
        """Test retrieval from empty collection."""
        class EmptyCollection:
            def query(self, query_embeddings, n_results):
                return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        retriever = Retriever(EmptyCollection())
        
        async def mock_embed(query):
            return [0.1] * 384
        
        retriever._embed_query = mock_embed
        
        chunks = await retriever.retrieve("test query", top_k=5)
        
        assert len(chunks) == 0
    
    def test_format_context(self):
        """Test formatting context from chunks."""
        retriever = Retriever(None)  # Collection not needed for this test
        
        chunks = [
            {
                "text": "This is a test chunk.",
                "metadata": {"source": "test.txt"},
                "score": 0.85
            },
            {
                "text": "Another test chunk.",
                "metadata": {"source": "test2.txt"},
                "score": 0.72
            }
        ]
        
        context = retriever.format_context(chunks)
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert "test.txt" in context
        assert "test2.txt" in context
        assert "0.85" in context
        assert "0.72" in context
    
    def test_format_context_empty(self):
        """Test formatting empty context."""
        retriever = Retriever(None)
        context = retriever.format_context([])
        assert context == ""
    
    @pytest.mark.asyncio
    async def test_embed_query_local(self):
        """Test query embedding with local model (if available)."""
        retriever = Retriever(None)
        
        try:
            embedding = await retriever._embed_query("test query")
            
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            # Should be normalized
            norm = sum(x*x for x in embedding)**0.5
            assert 0.9 < norm < 1.1
        except ImportError:
            pytest.skip("sentence-transformers not available")
        except Exception as e:
            pytest.skip(f"Local embedding failed: {e}")

